"""Durable archive of everything the radar decided was worth keeping.

GitHub Actions is ephemeral: without this, "what happened while I was away"
has no data to answer from. One gzip JSONL per month, appended daily, a few
hundred KB per month.
"""

from __future__ import annotations

import gzip
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .rank import Story

ARCHIVE_DIR = "data/archive"


def _month_path(when: datetime) -> Path:
    return Path(ARCHIVE_DIR) / f"{when:%Y-%m}.jsonl.gz"


def record(story: Story, when: datetime) -> dict:
    lead = story.lead
    return {
        "id": lead.id,
        "title": lead.title,
        "url": lead.url,
        "sources": sorted(story.sources),
        "topics": sorted(story.topics),
        "topic": lead.topic,
        "published": lead.published.isoformat() if lead.published else None,
        "score": round(story.score, 2),
        "taste": round(story.taste, 3),
        "engagement": int(story.total_engagement),
        "niche_hits": story.niche_hits,
        "meta": {k: v for k, v in lead.meta.items() if k != "taste"},
        "saved_at": when.isoformat(),
    }


def append(stories: list[Story], when: datetime | None = None) -> Path:
    when = when or datetime.now(timezone.utc)
    path = _month_path(when)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = {row["id"] for row in load_ids(path)}
    lines: list[str] = []
    for story in stories:
        row = record(story, when)
        if row["id"] in existing:
            continue
        existing.add(row["id"])
        lines.append(json.dumps(row, ensure_ascii=False))

    if lines:
        # gzip supports appended members; readers see one stream
        with gzip.open(path, "at", encoding="utf-8") as fh:
            for line in lines:
                fh.write(line + "\n")
    return path


def load_ids(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except (OSError, EOFError):
        return out
    return out


def months_between(start: datetime, end: datetime) -> list[Path]:
    paths: list[Path] = []
    cursor = start.replace(day=1)
    while cursor <= end:
        paths.append(_month_path(cursor))
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
    return paths


def load_range(days: int, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    rows: list[dict] = []
    seen: set[str] = set()
    for path in months_between(start, now):
        for row in load_ids(path):
            rid = row.get("id")
            if not rid or rid in seen:
                continue
            seen.add(rid)
            rows.append(row)
    return rows


def prune(keep_months: int = 12, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=keep_months * 31)).strftime("%Y-%m")
    removed = 0
    for path in Path(ARCHIVE_DIR).glob("*.jsonl.gz"):
        if path.name[:7] < cutoff:
            path.unlink()
            removed += 1
    return removed
