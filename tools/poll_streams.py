#!/usr/bin/env python3
"""Streams live-state + schedule poller.

Cron-invoked by .github/workflows/streams-poll.yaml every 5 min.
- Polls Twitch /helix/streams for live state (+ oauth dance).
- HEAD-probes youtube.com/channel/<id>/live for YT live state (0 Data-API quota).
- Once per hour: pulls Twitch /helix/schedule and writes streams-twitch-cache.yaml.
- On live→not-live transition: writes an auto-stub at content/streams/<slug>/index.md.

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


if __name__ == "__main__":
    sys.exit(0)  # placeholder; main() lands in Sub-task 34F
