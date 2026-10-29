"""Subreddit top-of-day, through the public Atom feed."""

from __future__ import annotations

from ..feed import parse_feed
from ..http import get
from ..models import Signal

_URL = "https://www.reddit.com/r/{sub}/top/.rss?t=day&limit=25"

# Reddit blocks browser-like UAs on the RSS endpoints; a descriptive one works.
_HEADERS = {"User-Agent": "tech-radar/1.0 (by /u/ab0_alhasan_)"}


def fetch(subreddits: list[str]) -> list[Signal]:
    out: list[Signal] = []
    for sub in subreddits:
        try:
            xml_text = get(_URL.format(sub=sub), headers=_HEADERS, min_gap=3.0)
        except RuntimeError as exc:
            print(f"[reddit] r/{sub}: {exc}")
            continue

        for item in parse_feed(xml_text):
            title = item["title"]
            if len(title) < 20:
                continue
            out.append(
                Signal(
                    title=title,
                    url=item["link"],
                    source="reddit",
                    topic="community",
                    published=item["published"],
                    summary=item["summary"][:400],
                    meta={"subreddit": f"r/{sub}"},
                )
            )
    return out
