"""Print the latest digest as a compact table (handy for a quick look)."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

data = json.loads(Path("data/latest.json").read_text("utf-8"))
stories = data["stories"]

counts: Counter = Counter()
for story in stories:
    counts.update(story.get("sources", []))

print(f"generated: {data['generated_at']}  fetched: {data['fetched']}")
print(f"sources: {dict(counts)}")
print("-" * 100)
for story in stories:
    src = ",".join(story.get("sources", []))
    print(f"{story['score']:5.1f} | {src:<16} | {story['title'][:110]}")
