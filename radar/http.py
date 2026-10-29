"""Tiny stdlib HTTP helper — no third-party dependency, works on a bare runner."""

from __future__ import annotations

import gzip
import json
import time
import urllib.error
import urllib.request
import zlib

from .config import REQUEST_TIMEOUT, USER_AGENT

_last_call = 0.0


def _throttle(min_gap: float) -> None:
    global _last_call
    wait = min_gap - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.monotonic()


def get(url: str, *, headers: dict | None = None, min_gap: float = 1.0) -> str:
    """GET a URL and return decoded text. Raises on HTTP errors."""
    _throttle(min_gap)
    req_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate",
    }
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read()
            encoding = (resp.headers.get("Content-Encoding") or "").lower()
            if encoding == "gzip":
                raw = gzip.decompress(raw)
            elif encoding == "deflate":
                raw = zlib.decompress(raw)
            charset = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"network error for {url}: {exc.reason}") from exc


def get_json(url: str, *, headers: dict | None = None, min_gap: float = 1.0):
    text = get(url, headers=headers, min_gap=min_gap)
    return json.loads(text)
