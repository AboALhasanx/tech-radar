"""Posts from the curated researcher accounts.

The list lives in ``radar/curated.json``. A local run of
``python tools/x_session.py accounts`` refreshes ``data/x_accounts.json`` with a
logged-in browser; this module only reads that file, so it also works on a
runner.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..feed import parse_date
from ..models import Signal

PATH = Path("data/x_accounts.json")


def _likes(value: str) -> int:
    value = (value or "0").strip().replace(",", "")
    if not value:
        return 0
    mult = 1
    if value[-1] in "Kk":
        mult, value = 1000, value[:-1]
    elif value[-1] in "Mm":
        mult, value = 1_000_000, value[:-1]
    try:
        return int(float(value) * mult)
    except ValueError:
        return 0


def fetch(path: Path = PATH) -> list[Signal]:
    if not path.exists():
        return []
    try:
        rows = json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError:
        return []

    out: list[Signal] = []
    for row in rows:
        text = (row.get("text") or "").replace("\n", " ").strip()
        if len(text) < 40:
            continue
        author = (row.get("author") or "").strip()
        out.append(
            Signal(
                title=text[:200],
                url=row.get("url") or "",
                source="x_account",
                topic="research_tools",
                published=parse_date(row.get("when")),
                summary=text[:400],
                engagement=float(_likes(row.get("likes", "0"))),
                meta={"author": author},
            )
        )
    return out
