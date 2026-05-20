"""Tests for tools/poll_streams.py — run with:
   python3 -m unittest tools/test_poll_streams.py -v

All network calls are mocked via unittest.mock.patch on urllib.request.urlopen.
"""
from __future__ import annotations

import io
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
