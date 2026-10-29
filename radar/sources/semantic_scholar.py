"""Semantic Scholar — search by topic, not by date.

Used for the four or five research questions this profile actually tracks, so
the digest can surface a paper that is not on today's arXiv list.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from ..feed import parse_date
from ..http import get_json
from ..models import Signal

_BASE = (
    "https://api.semanticscholar.org/graph/v1/paper/search"
    "?query={q}&limit={limit}&fields=title,url,abstract,citationCount,publicationDate,externalIds"
)


def fetch(queries: list[tuple[str, str]] | None = None, limit: int = 8) -> list[Signal]:
    out: list[Signal] = []
    for topic, query in queries or []:
        url = _BASE.format(q=quote_plus(query), limit=limit)
        try:
            data = get_json(url, min_gap=3.5)
        except RuntimeError as exc:
            print(f"[s2] {topic}: {exc}")
            continue

        for paper in data.get("data", []):
            title = (paper.get("title") or "").strip()
            if len(title) < 20:
                continue
            link = paper.get("url") or ""
            doi = (paper.get("externalIds") or {}).get("DOI")
            if doi:
                link = f"https://doi.org/{doi}"
            out.append(
                Signal(
                    title=title,
                    url=link,
                    source="paper",
                    topic="research",
                    published=parse_date(paper.get("publicationDate")),
                    summary=(paper.get("abstract") or "")[:400],
                    engagement=float(paper.get("citationCount") or 0),
                    meta={"query": query},
                )
            )
    return out
