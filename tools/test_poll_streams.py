"""Tests for tools/poll_streams.py — run with:
   python3 -m unittest tools/test_poll_streams.py -v

All network calls are mocked via unittest.mock.patch on urllib.request.urlopen.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import poll_streams as ps  # noqa: E402


def _mock_response(body, status=200, headers=None):
    """Helper: build a fake urllib HTTPResponse-like object."""
    resp = MagicMock()
    resp.read.return_value = body.encode("utf-8") if isinstance(body, str) else body
    resp.status = status
    resp.getcode.return_value = status
    resp.headers = headers or {}
    resp.__enter__ = lambda self_: self_
    resp.__exit__ = lambda *a: None
    return resp


class TwitchOAuthTests(unittest.TestCase):
    @patch("poll_streams.urllib.request.urlopen")
    def test_oauth_returns_access_token(self, mock_open):
        mock_open.return_value = _mock_response(json.dumps({
            "access_token": "tok-abc",
            "expires_in": 5184000,
            "token_type": "bearer",
        }))
        token = ps.twitch_oauth("client-id", "client-secret")
        self.assertEqual(token, "tok-abc")

    @patch("poll_streams.urllib.request.urlopen")
    def test_oauth_raises_on_missing_token(self, mock_open):
        mock_open.return_value = _mock_response(json.dumps({"error": "denied"}))
        with self.assertRaises(ps.PollError):
            ps.twitch_oauth("client-id", "client-secret")


class TwitchLiveStateTests(unittest.TestCase):
    @patch("poll_streams.urllib.request.urlopen")
    def test_twitch_streams_live(self, mock_open):
        mock_open.return_value = _mock_response(json.dumps({
            "data": [{
                "type": "live",
                "title": "Example live stream",
                "started_at": "2026-04-10T19:00:00Z",
                "user_login": "a3madkour",
            }],
        }))
        state = ps.twitch_live_state("tok-abc", "client-id", "a3madkour")
        self.assertTrue(state["is_live"])
        self.assertEqual(state["title"], "Example live stream")
        self.assertEqual(state["started_at"], "2026-04-10T19:00:00Z")
        self.assertEqual(state["url"], "https://twitch.tv/a3madkour")

    @patch("poll_streams.urllib.request.urlopen")
    def test_twitch_streams_not_live(self, mock_open):
        mock_open.return_value = _mock_response(json.dumps({"data": []}))
        state = ps.twitch_live_state("tok-abc", "client-id", "a3madkour")
        self.assertFalse(state["is_live"])
        self.assertEqual(state["title"], "")
        self.assertEqual(state["url"], "")


class YouTubeLiveProbeTests(unittest.TestCase):
    @patch("poll_streams._http_head_no_follow")
    def test_youtube_live_200(self, mock_head):
        mock_head.return_value = 200
        self.assertTrue(ps.youtube_is_live("UC-abc"))

    @patch("poll_streams._http_head_no_follow")
    def test_youtube_live_302(self, mock_head):
        # 302 redirect = currently live (YouTube redirects /channel/<id>/live to /watch?v=...)
        mock_head.return_value = 302
        self.assertTrue(ps.youtube_is_live("UC-abc"))

    @patch("poll_streams._http_head_no_follow")
    def test_youtube_not_live_404(self, mock_head):
        mock_head.return_value = 404
        self.assertFalse(ps.youtube_is_live("UC-abc"))

    @patch("poll_streams._http_head_no_follow")
    def test_youtube_not_live_other(self, mock_head):
        mock_head.return_value = 500
        self.assertFalse(ps.youtube_is_live("UC-abc"))


class AutoStubTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_creates_stub_when_absent(self):
        ps.write_auto_stub(
            content_root=self.tmp / "content",
            title="Example live coding stream",
            started_at_iso="2026-04-10T19:00:00Z",
        )
        path = self.tmp / "content" / "streams" / "2026-04-10-example-live-coding-stream" / "index.md"
        self.assertTrue(path.exists())
        text = path.read_text()
        self.assertIn('title: "Example live coding stream"', text)
        self.assertIn("archive_status: archived", text)
        self.assertIn("draft: true", text)
        self.assertIn("category: game-dev", text)
        self.assertIn("platforms: [twitch, youtube]", text)
        self.assertIn('date: 2026-04-10T19:00:00', text)

    def test_idempotent_does_not_overwrite(self):
        path = self.tmp / "content" / "streams" / "2026-04-10-already-here" / "index.md"
        path.parent.mkdir(parents=True)
        path.write_text("---\ntitle: \"Hand-edited\"\n---\nuser content\n")
        ps.write_auto_stub(
            content_root=self.tmp / "content",
            title="already here",
            started_at_iso="2026-04-10T19:00:00Z",
        )
        self.assertIn("user content", path.read_text())

    def test_slugify_strips_punctuation_and_lowercases(self):
        # Title with mixed case + punctuation + multiple spaces.
        slug = ps.slugify("Game Dev: HEX grid (prototype)!")
        # Expected: lowercase, ascii-only kebab.
        self.assertEqual(slug, "game-dev-hex-grid-prototype")

    def test_slug_path_uses_date_prefix(self):
        slug_path = ps.stub_path(
            content_root=self.tmp / "content",
            title="X y z",
            started_at_iso="2026-05-19T14:30:00Z",
        )
        self.assertEqual(
            slug_path,
            self.tmp / "content" / "streams" / "2026-05-19-x-y-z" / "index.md",
        )


class LiveStateIOTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_write_live_yaml(self):
        twitch = {"is_live": True, "title": "x", "started_at": "2026-04-10T19:00:00Z", "url": "https://twitch.tv/x"}
        youtube = {"is_live": True, "video_id": "abc", "title": "x", "started_at": "2026-04-10T19:00:00Z", "url": "https://www.youtube.com/watch?v=abc"}
        ps.write_live_yaml(self.tmp / "data" / "streams-live.yaml",
                           polled_at="2026-04-10T19:00:30Z",
                           twitch=twitch, youtube=youtube)
        text = (self.tmp / "data" / "streams-live.yaml").read_text()
        self.assertIn("last_polled: 2026-04-10T19:00:30Z", text)
        self.assertIn("is_live: true", text)
        self.assertIn('video_id: "abc"', text)

    def test_read_prior_live_yaml(self):
        d = self.tmp / "data"
        d.mkdir()
        (d / "streams-live.yaml").write_text(
            "last_polled: 2026-04-10T18:55:00Z\n"
            "live:\n"
            "  twitch:\n"
            "    is_live: true\n"
            "    title: \"prior session\"\n"
            "    started_at: \"2026-04-10T18:00:00Z\"\n"
            "    url: \"https://twitch.tv/x\"\n"
            "  youtube:\n"
            "    is_live: false\n"
            "    video_id: \"\"\n"
            "    title: \"\"\n"
            "    started_at: \"\"\n"
            "    url: \"\"\n"
        )
        prior = ps.read_live_yaml(d / "streams-live.yaml")
        self.assertTrue(prior["twitch"]["is_live"])
        self.assertEqual(prior["twitch"]["title"], "prior session")
        self.assertFalse(prior["youtube"]["is_live"])

    def test_read_missing_returns_default_not_live(self):
        prior = ps.read_live_yaml(self.tmp / "absent.yaml")
        self.assertFalse(prior["twitch"]["is_live"])
        self.assertFalse(prior["youtube"]["is_live"])


class MainOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "data").mkdir()
        (self.tmp / "content").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    @patch("poll_streams.youtube_is_live")
    @patch("poll_streams.twitch_live_state")
    @patch("poll_streams.twitch_oauth")
    def test_live_to_not_live_writes_stub(self, mock_oauth, mock_tw, mock_yt):
        # Seed prior state: Twitch was live, with a title and started_at.
        (self.tmp / "data" / "streams-live.yaml").write_text(
            "last_polled: 2026-04-10T18:55:00Z\n"
            "live:\n"
            "  twitch:\n"
            "    is_live: true\n"
            '    title: "Example live coding stream"\n'
            '    started_at: "2026-04-10T18:00:00Z"\n'
            '    url: "https://twitch.tv/x"\n'
            "  youtube:\n"
            "    is_live: false\n"
            '    video_id: ""\n'
            '    title: ""\n'
            '    started_at: ""\n'
            '    url: ""\n'
        )
        mock_oauth.return_value = "tok"
        mock_tw.return_value = {"is_live": False, "title": "", "started_at": "", "url": ""}
        mock_yt.return_value = False
        env = {
            "TWITCH_CLIENT_ID": "cid",
            "TWITCH_CLIENT_SECRET": "csec",
            "TWITCH_USER_LOGIN": "x",
            "YOUTUBE_CHANNEL_ID": "UC-y",
            "YOUTUBE_API_KEY": "yk",  # unused but tolerated
        }
        rc = ps.main(repo_root=self.tmp, env=env, now_iso="2026-04-10T19:30:00Z")
        self.assertEqual(rc, 0)
        # A stub should have been created from the prior live state's title + started_at.
        stub = self.tmp / "content" / "streams" / "2026-04-10-example-live-coding-stream" / "index.md"
        self.assertTrue(stub.exists())
        # live.yaml should now reflect not-live.
        text = (self.tmp / "data" / "streams-live.yaml").read_text()
        self.assertIn("is_live: false", text)

    @patch("poll_streams.youtube_is_live")
    @patch("poll_streams.twitch_live_state")
    @patch("poll_streams.twitch_oauth")
    def test_not_live_to_live_no_stub(self, mock_oauth, mock_tw, mock_yt):
        # No prior live yaml → first poll, transition to live.
        mock_oauth.return_value = "tok"
        mock_tw.return_value = {"is_live": True, "title": "fresh", "started_at": "2026-04-10T20:00:00Z", "url": "https://twitch.tv/x"}
        mock_yt.return_value = True
        env = {
            "TWITCH_CLIENT_ID": "cid", "TWITCH_CLIENT_SECRET": "csec",
            "TWITCH_USER_LOGIN": "x", "YOUTUBE_CHANNEL_ID": "UC-y", "YOUTUBE_API_KEY": "yk",
        }
        rc = ps.main(repo_root=self.tmp, env=env, now_iso="2026-04-10T20:01:00Z")
        self.assertEqual(rc, 0)
        # No stubs created on go-live.
        self.assertFalse((self.tmp / "content" / "streams").exists() and any((self.tmp / "content" / "streams").iterdir()))
        text = (self.tmp / "data" / "streams-live.yaml").read_text()
        self.assertIn("is_live: true", text)

    @patch("poll_streams.youtube_is_live")
    @patch("poll_streams.twitch_live_state", side_effect=Exception("transient!"))
    @patch("poll_streams.twitch_oauth")
    def test_transient_api_failure_exits_0(self, mock_oauth, mock_tw, mock_yt):
        mock_oauth.return_value = "tok"
        mock_yt.return_value = False
        env = {
            "TWITCH_CLIENT_ID": "cid", "TWITCH_CLIENT_SECRET": "csec",
            "TWITCH_USER_LOGIN": "x", "YOUTUBE_CHANNEL_ID": "UC-y", "YOUTUBE_API_KEY": "yk",
        }
        rc = ps.main(repo_root=self.tmp, env=env, now_iso="2026-04-10T20:01:00Z")
        self.assertEqual(rc, 0)

    def test_missing_secret_exits_nonzero(self):
        rc = ps.main(repo_root=self.tmp, env={}, now_iso="2026-04-10T20:01:00Z")
        self.assertNotEqual(rc, 0)
