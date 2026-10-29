"""Product Hunt — the launch surface.

Most "tool that helps researchers" news arrives here first. The RSS feed is
free and keyless.
"""

from __future__ import annotations

from ..feed import parse_feed
from ..http import get
from ..models import Signal

_URL = "https://www.producthunt.com/feed"


def fetch(limit: int = 40) -> list[Signal]:
    try:
        xml_text = get(_URL, min_gap=1.0)
    except RuntimeError as exc:
        print(f"[producthunt] {exc}")
        return []

    out: list[Signal] = []
    for item in parse_feed(xml_text)[:limit]:
        title = item["title"]
        if len(title) < 8:
            continue
        out.append(
            Signal(
                title=title,
                url=item["link"],
                source="producthunt",
                topic="launch",
                published=item["published"],
                summary=item["summary"][:300],
                meta={"via": "Product Hunt"},
            )
        )
    return out
