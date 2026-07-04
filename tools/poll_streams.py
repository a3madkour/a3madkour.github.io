#!/usr/bin/env python3
"""Streams live-state poller.

Cron-invoked by .github/workflows/streams-poll.yaml every 5 min.
- Polls Twitch /helix/streams for live state (+ oauth dance).
- HEAD-probes youtube.com/channel/<id>/live for YT live state (0 Data-API quota).
- On live→not-live transition: writes an auto-stub at content/streams/<slug>/index.md.

(Spec §5 step 4 — hourly Twitch /helix/schedule poll → data/streams-twitch-cache.yaml —
is deferred to a follow-up; data/streams-schedule.yaml is user-authored and covers
current UX needs.)

Spec: docs/superpowers/specs/2026-05-13-streams-section-design.md §5.
Stdlib only. Always exits 0 on transient API failures (preserves prior yaml).
Exits non-zero only on auth-config errors.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class PollError(Exception):
    """Raised on auth-config or contract violations that must NOT silently 0-exit."""


# --- Twitch ---

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_STREAMS_URL = "https://api.twitch.tv/helix/streams"
# Reserved for the deferred hourly schedule-cache subtask (see docstring + plan).
TWITCH_SCHEDULE_URL = "https://api.twitch.tv/helix/schedule"
YOUTUBE_LIVE_URL_TEMPLATE = "https://www.youtube.com/channel/{channel_id}/live"


def _http_post_form(url: str, body: dict) -> Any:
    data = urllib.parse.urlencode(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    return urllib.request.urlopen(req, timeout=10)


def _http_get(url: str, headers: dict | None = None) -> Any:
    req = urllib.request.Request(url, method="GET", headers=headers or {})
    return urllib.request.urlopen(req, timeout=10)


def _http_head_no_follow(url: str) -> int:
    """Return HTTP status code from a HEAD request without following redirects."""
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **kw):
            return None
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, method="HEAD")
    try:
        with opener.open(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def twitch_oauth(client_id: str, client_secret: str) -> str:
    """Client-credentials grant. Returns access token. Raises PollError on failure."""
    resp = _http_post_form(TWITCH_TOKEN_URL, {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    })
    with resp:
        payload = json.loads(resp.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        raise PollError(f"twitch oauth: no access_token in response: {payload!r}")
    return token


def twitch_live_state(token: str, client_id: str, user_login: str) -> dict:
    """Return {is_live, title, started_at, url} for a Twitch user."""
    url = f"{TWITCH_STREAMS_URL}?{urllib.parse.urlencode({'user_login': user_login})}"
    resp = _http_get(url, headers={
        "Authorization": f"Bearer {token}",
        "Client-Id": client_id,
    })
    with resp:
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data") or []
    if not data or data[0].get("type") != "live":
        return {"is_live": False, "title": "", "started_at": "", "url": ""}
    entry = data[0]
    return {
        "is_live": True,
        "title": entry.get("title", ""),
        "started_at": entry.get("started_at", ""),
        "url": f"https://twitch.tv/{user_login}",
    }


def youtube_is_live(channel_id: str) -> bool:
    """HEAD-probe youtube.com/channel/<id>/live. 200 or 3xx = live."""
    url = YOUTUBE_LIVE_URL_TEMPLATE.format(channel_id=channel_id)
    status = _http_head_no_follow(url)
    return status == 200 or (300 <= status < 400)


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = _SLUG_RE.sub("-", s)
    return s.strip("-")


def _date_prefix(started_at_iso: str) -> str:
    """Return YYYY-MM-DD from an RFC3339 / ISO8601 timestamp."""
    # Parse the date portion (first 10 chars) — robust enough for Twitch responses.
    return started_at_iso[:10]


def stub_path(content_root: Path, title: str, started_at_iso: str) -> Path:
    slug = f"{_date_prefix(started_at_iso)}-{slugify(title)}"
    return content_root / "streams" / slug / "index.md"


def write_auto_stub(content_root: Path, title: str, started_at_iso: str) -> Path:
    """Create content/streams/<YYYY-MM-DD>-<slug>/index.md if absent (idempotent).

    Defaults: category=game-dev (user edits post-hoc), archive_status=archived,
    draft=true, platforms=[twitch,youtube], empty vod_url + show notes."""
    path = stub_path(content_root, title, started_at_iso)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_title = title.replace('"', '\\"')
    body = (
        "---\n"
        f'title: "{safe_title}"\n'
        f"date: {started_at_iso}\n"
        "duration: \"\"\n"
        "platforms: [twitch, youtube]\n"
        "vod_url: \"\"\n"
        "twitch_archive_url: \"\"\n"
        "archive_url: \"\"\n"
        "archive_status: archived\n"
        "category: game-dev\n"
        "tags: []\n"
        "summary: \"\"\n"
        "related_essays: []\n"
        "related_garden: []\n"
        "related_research: []\n"
        "related_works: []\n"
        "draft: true\n"
        "---\n"
        "\n"
        "Show notes — fill in.\n"
    )
    path.write_text(body)
    return path


def write_live_yaml(path: Path, polled_at: str, twitch: dict, youtube: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml = (
        f"last_polled: {polled_at}\n"
        "live:\n"
        "  twitch:\n"
        f"    is_live: {'true' if twitch['is_live'] else 'false'}\n"
        f"    title: {json.dumps(twitch.get('title', ''))}\n"
        f"    started_at: {json.dumps(twitch.get('started_at', ''))}\n"
        f"    url: {json.dumps(twitch.get('url', ''))}\n"
        "  youtube:\n"
        f"    is_live: {'true' if youtube['is_live'] else 'false'}\n"
        f"    video_id: {json.dumps(youtube.get('video_id', ''))}\n"
        f"    title: {json.dumps(youtube.get('title', ''))}\n"
        f"    started_at: {json.dumps(youtube.get('started_at', ''))}\n"
        f"    url: {json.dumps(youtube.get('url', ''))}\n"
    )
    path.write_text(yaml)


_BOOL_RE = re.compile(r"is_live:\s*(true|false)", re.IGNORECASE)
_QUOTED_RE = re.compile(r'^\s*(\w+):\s*"([^"]*)"\s*$')


def read_live_yaml(path: Path) -> dict:
    """Best-effort stdlib YAML read. Returns
    {twitch:{is_live,title,started_at,url}, youtube:{is_live,video_id,title,started_at,url}}."""
    default = {
        "twitch":  {"is_live": False, "title": "", "started_at": "", "url": ""},
        "youtube": {"is_live": False, "video_id": "", "title": "", "started_at": "", "url": ""},
    }
    if not path.exists():
        return default
    text = path.read_text()
    out = default
    section = None
    for raw in text.splitlines():
        s = raw.strip()
        if s == "twitch:":
            section = "twitch"
            continue
        if s == "youtube:":
            section = "youtube"
            continue
        if section is None:
            continue
        if s.startswith("is_live:"):
            m = _BOOL_RE.search(s)
            out[section]["is_live"] = bool(m and m.group(1).lower() == "true")
            continue
        m = _QUOTED_RE.match(raw)
        if m:
            k, v = m.group(1), m.group(2)
            if k in out[section]:
                out[section][k] = v
    return out


REQUIRED_ENV = ("TWITCH_CLIENT_ID", "TWITCH_CLIENT_SECRET", "TWITCH_USER_LOGIN", "YOUTUBE_CHANNEL_ID")


def main(repo_root: Path | None = None, env: dict | None = None, now_iso: str | None = None) -> int:
    repo_root = repo_root or Path(__file__).resolve().parent.parent
    env = env if env is not None else os.environ
    now_iso = now_iso or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    missing = [k for k in REQUIRED_ENV if not env.get(k)]
    if missing:
        print(f"poll_streams: missing required env: {missing}", file=sys.stderr)
        return 2

    live_yaml = repo_root / "data" / "streams-live.yaml"
    prior = read_live_yaml(live_yaml)

    # --- Twitch ---
    twitch_state = {"is_live": False, "title": "", "started_at": "", "url": ""}
    try:
        token = twitch_oauth(env["TWITCH_CLIENT_ID"], env["TWITCH_CLIENT_SECRET"])
        twitch_state = twitch_live_state(token, env["TWITCH_CLIENT_ID"], env["TWITCH_USER_LOGIN"])
    except PollError as e:
        print(f"poll_streams: twitch error (non-fatal): {e}", file=sys.stderr)
        twitch_state = prior["twitch"]   # preserve prior state on auth blip
    except Exception as e:  # noqa: BLE001 — transient HTTP, DNS, etc.
        print(f"poll_streams: twitch transient: {e}", file=sys.stderr)
        twitch_state = prior["twitch"]

    # --- YouTube ---
    yt_is_live = False
    try:
        yt_is_live = youtube_is_live(env["YOUTUBE_CHANNEL_ID"])
    except Exception as e:  # noqa: BLE001
        print(f"poll_streams: youtube transient: {e}", file=sys.stderr)
        yt_is_live = prior["youtube"]["is_live"]
    youtube_state = {
        "is_live": yt_is_live,
        "video_id": prior["youtube"]["video_id"] if yt_is_live else "",
        "title": prior["youtube"]["title"] if yt_is_live else "",
        "started_at": prior["youtube"]["started_at"] if yt_is_live else "",
        "url": f"https://www.youtube.com/channel/{env['YOUTUBE_CHANNEL_ID']}/live" if yt_is_live else "",
    }

    # --- Transition: live → not-live on Twitch ⇒ auto-stub from prior state ---
    if prior["twitch"]["is_live"] and not twitch_state["is_live"]:
        title = prior["twitch"]["title"] or "Untitled stream"
        started = prior["twitch"]["started_at"] or now_iso
        try:
            write_auto_stub(repo_root / "content", title, started)
        except Exception as e:  # noqa: BLE001
            print(f"poll_streams: stub write failed (non-fatal): {e}", file=sys.stderr)

    # Only rewrite the file when the meaningful live-state actually changed.
    # last_polled alone must not churn — otherwise the cron commits+pushes to
    # master every 5 minutes (288/day) with no real content change.
    changed = twitch_state != prior["twitch"] or youtube_state != prior["youtube"]
    if changed or not live_yaml.exists():
        write_live_yaml(live_yaml, polled_at=now_iso,
                        twitch=twitch_state, youtube=youtube_state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
