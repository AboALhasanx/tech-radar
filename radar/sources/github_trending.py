"""New and fast-rising repositories, via the GitHub search API.

The trending page has no API and changes markup; the search API gives the same
signal (young repos with a lot of stars) in a stable shape.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from ..feed import parse_date
from ..http import get_json
from ..models import Signal

_URL = (
    "https://api.github.com/search/repositories"
    "?q=created:>{since}+stars:>{stars}&sort=stars&order=desc&per_page=25"
)


def fetch(min_stars: int = 40, window_days: int = 7) -> list[Signal]:
    since = (datetime.now(timezone.utc) - timedelta(days=window_days)).strftime("%Y-%m-%d")
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        data = get_json(_URL.format(since=since, stars=min_stars), headers=headers)
    except RuntimeError as exc:
        print(f"[github] {exc}")
        return []

    out: list[Signal] = []
    for repo in data.get("items", []):
        name = repo.get("full_name") or ""
        desc = (repo.get("description") or "").strip()
        stars = int(repo.get("stargazers_count") or 0)
        stars_today = repo.get("star", 0)
        out.append(
            Signal(
                title=f"{name} — {desc}" if desc else name,
                url=repo.get("html_url") or "",
                source="github",
                topic="code",
                published=parse_date(repo.get("created_at")),
                engagement=float(stars),
                meta={
                    "repo": name,
                    "stars": stars,
                    "stars_today": stars_today,
                    "language": repo.get("language"),
                    "topics": repo.get("topics") or [],
                },
            )
        )
    return out
