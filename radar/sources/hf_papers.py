"""Hugging Face daily papers — the highest-signal free research feed.

50 papers a day, each with an AI summary, keywords, an upvote count and often
the GitHub repo. No key, no quota.
"""

from __future__ import annotations

from ..feed import parse_date
from ..http import get_json
from ..models import Signal

_URL = "https://huggingface.co/api/daily_papers"


def fetch(min_upvotes: int = 0) -> list[Signal]:
    try:
        data = get_json(_URL, min_gap=1.0)
    except RuntimeError as exc:
        print(f"[hf-papers] {exc}")
        return []

    out: list[Signal] = []
    for entry in data:
        paper = entry.get("paper") or {}
        title = (paper.get("title") or entry.get("title") or "").strip()
        if not title:
            continue
        upvotes = int(paper.get("upvotes") or 0)
        if upvotes < min_upvotes:
            continue

        pid = paper.get("id") or ""
        url = f"https://huggingface.co/papers/{pid}" if pid else ""
        keywords = paper.get("ai_keywords") or []
        repo = paper.get("githubRepo") or ""

        out.append(
            Signal(
                title=title,
                url=url,
                source="paper",
                topic="research",
                published=parse_date(entry.get("publishedAt") or paper.get("publishedAt")),
                summary=(paper.get("ai_summary") or paper.get("summary") or "")[:400],
                engagement=float(upvotes + int(paper.get("githubStars") or 0)),
                meta={
                    "repo": repo.replace("https://github.com/", "") if repo else "",
                    "keywords": keywords[:6],
                    "arxiv": pid,
                },
            )
        )
    return out
