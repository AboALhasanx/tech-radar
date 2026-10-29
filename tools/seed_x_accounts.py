"""Seed data/x_accounts.json from the history already scraped.

Useful when the browser is open (cookie jar locked) or when you simply want the
radar to start using the curated accounts without another scrape.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CURATED = json.loads((ROOT / "radar" / "curated.json").read_text("utf-8"))
HISTORY = ROOT / "data" / "x_history_60d.json"
OUT = ROOT / "data" / "x_accounts.json"

handles = {a["handle"].lstrip("@").lower() for a in CURATED.get("x_accounts", [])}
if not HISTORY.exists():
    print(f"missing {HISTORY}; run tools/x_session.py history first")
    raise SystemExit(1)

rows = json.loads(HISTORY.read_text("utf-8"))
picked = []
for row in rows:
    author = (row.get("author") or "").lower()
    if any(h in author for h in handles):
        picked.append(row)

merged = {r["url"]: r for r in picked if r.get("url")}
if OUT.exists():
    try:
        for row in json.loads(OUT.read_text("utf-8")):
            if row.get("url"):
                merged.setdefault(row["url"], row)
    except json.JSONDecodeError:
        pass

out = sorted(merged.values(), key=lambda r: r.get("when") or "", reverse=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[seed] {len(picked)} matches from history -> {len(out)} rows in {OUT}")
for row in out[:10]:
    print(f"  {row.get('when','')[:10]} {row.get('author','')[:40]} {row.get('text','')[:70]}")
