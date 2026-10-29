"""Curated research newsletters.

The radar follows people, not only keywords: a handful of writers consistently
surface the tooling shift before it becomes a trend.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..feed import parse_feed
from ..http import get
from ..models import Signal

CURATED = Path(__file__).resolve().parent.parent / "curated.json"


def load() -> dict:
    if not CURATED.exists():
        return {"newsletters": []}
    return json.loads(CURATED.read_text("utf-8"))


def fetch(limit_per_feed: int = 4) -> list[Signal]:
    out: list[Signal] = []
    for feed in load().get("newsletters", []):
        try:
            xml_text = get(feed["url"], min_gap=2.0)
        except RuntimeError as exc:
            print(f"[newsletter] {feed['name']}: {exc}")
            continue

        for item in parse_feed(xml_text)[:limit_per_feed]:
            title = item["title"]
            if len(title) < 15:
                continue
            out.append(
                Signal(
                    title=title,
                    url=item["link"],
                    source="newsletter",
                    topic=feed.get("focus", "research"),
                    published=item["published"],
                    summary=item["summary"][:400],
                    meta={"outlet": feed["name"]},
                )
            )
    return out
