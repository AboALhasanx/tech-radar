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
