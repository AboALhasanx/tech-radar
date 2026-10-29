"""GitHub repos that are research *tooling* — the thing researchers install.

Topic search is used instead of a keyword search so results are tools people
actually tag, not papers that mention a tool.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from ..feed import parse_date
from ..http import get_json
from ..models import Signal

_BASE = (
    "https://api.github.com/search/repositories"
    "?q={q}&sort=stars&order=desc&per_page={n}"
)

QUERIES = [
    "topic:research-tools",
    "topic:academic",
    "topic:literature-review",
    "topic:scientific-writing",
    "topic:zotero",
    'zotero-mcp in:name',
    '"literature review" in:description',
]


def fetch(per_query: int = 6, min_stars: int = 30, window_days: int = 180) -> list[Signal]:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    since = (datetime.now(timezone.utc) - timedelta(days=window_days)).strftime("%Y-%m-%d")
    out: list[Signal] = []
    for base in QUERIES:
        q = f"{base} stars:>{min_stars} pushed:>{since}"
        url = _BASE.format(q=q.replace(" ", "+"), n=per_query)
        try:
            data = get_json(url, headers=headers, min_gap=2.5)
        except RuntimeError as exc:
            print(f"[gh-tools] {base}: {exc}")
            continue

        for repo in data.get("items", []):
            name = repo.get("full_name") or ""
            desc = (repo.get("description") or "").strip()
            out.append(
                Signal(
                    title=f"{name} — {desc}" if desc else name,
                    url=repo.get("html_url") or "",
                    source="github",
                    topic="research_tools",
                    published=parse_date(repo.get("created_at")),
                    engagement=float(repo.get("stargazers_count") or 0),
                    meta={
                        "repo": name,
                        "stars": repo.get("stargazers_count") or 0,
                        "language": repo.get("language"),
                    },
                )
            )
    return out
