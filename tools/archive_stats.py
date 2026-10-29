"""Quick stats over the archive: what is in it, and what ranks highest."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from radar import archive  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
source_filter = sys.argv[2] if len(sys.argv) > 2 else None
rows = archive.load_range(days)
topics: Counter = Counter()
sources: Counter = Counter()
for row in rows:
    topics[row.get("topic") or "?"] += 1
    for s in row.get("sources") or []:
        sources[s] += 1

print(f"rows: {len(rows)}")
print("topics:", dict(topics.most_common()))
print("sources:", dict(sources.most_common()))
print("\nresearch rows:")
for row in sorted(
    (r for r in rows if (r.get("topics") or []) and set(r["topics"]) & {"research", "writing", "reasoning", "learning"}),
    key=lambda r: -r.get("score", 0),
)[:15]:
    print(f"  {row.get('score', 0):5.1f} {row.get('topic'):10} {row['title'][:90]}")

if source_filter:
    print(f"\n{source_filter} rows:")
    picked = [r for r in rows if source_filter in (r.get("sources") or [])]
    for row in sorted(picked, key=lambda r: -r.get("score", 0))[:15]:
        print(f"  {row.get('score', 0):5.1f} taste={row.get('taste', 0):.2f} {row['title'][:90]}")
