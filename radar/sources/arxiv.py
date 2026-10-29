"""arXiv RSS — the announcement stream, not a search.

RSS is used instead of the API because it is one request per category and
already filtered to what was announced today.
"""

from __future__ import annotations

from ..feed import parse_feed
from ..http import get
from ..models import Signal

FEEDS = [
    ("cs.CL", "https://rss.arxiv.org/rss/cs.CL"),
    ("cs.AI", "https://rss.arxiv.org/rss/cs.AI"),
    ("cs.SE", "https://rss.arxiv.org/rss/cs.SE"),
    ("cs.HC", "https://rss.arxiv.org/rss/cs.HC"),
]

MAX_PER_FEED = 20


def fetch(feeds: list[tuple[str, str]] | None = None) -> list[Signal]:
    out: list[Signal] = []
    for name, url in feeds or FEEDS:
        try:
            xml_text = get(url, min_gap=3.0)
        except RuntimeError as exc:
            print(f"[arxiv] {name}: {exc}")
            continue

        for item in parse_feed(xml_text)[:MAX_PER_FEED]:
            title = item["title"]
            # arXiv prefixes titles with an announcement tag
            title = title.replace("arXiv:", "").strip()
            if len(title) < 20:
                continue
            out.append(
                Signal(
                    title=title,
                    url=item["link"],
                    source="paper",
                    topic="research",
                    published=item["published"],
                    summary=item["summary"][:400],
                    meta={"venue": f"arXiv {name}"},
                )
            )
    return out
