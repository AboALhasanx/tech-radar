"""Hacker News front page via the free Algolia API."""

from __future__ import annotations

from ..feed import parse_date
from ..http import get_json
from ..models import Signal

_URL = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=40"


def fetch(min_points: int = 80) -> list[Signal]:
    try:
        data = get_json(_URL)
    except RuntimeError as exc:
        print(f"[hackernews] {exc}")
        return []

    out: list[Signal] = []
    for hit in data.get("hits", []):
        points = int(hit.get("points") or 0)
        if points < min_points:
            continue
        title = (hit.get("title") or "").strip()
        link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        out.append(
            Signal(
                title=title,
                url=link,
                source="hackernews",
                topic="dev",
                published=parse_date(hit.get("created_at")),
                engagement=float(points),
                meta={
                    "points": points,
                    "comments": hit.get("num_comments") or 0,
                    "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                },
            )
        )
    return out
