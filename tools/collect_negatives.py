"""Collect easy negatives: public X posts about things this account does not read."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from radar.sources.google_news import _fetch  # noqa: E402

QUERIES = [
    ("sports", 'site:x.com (NBA OR NFL OR MLB OR soccer OR "World Series") when:30d'),
    ("ent", 'site:x.com (movie OR album OR celebrity OR concert OR "box office") when:30d'),
    ("politics", 'site:x.com (election OR senator OR parliament OR president) when:30d'),
    ("life", 'site:x.com (recipe OR travel OR fashion OR wedding) when:30d'),
]


def main() -> int:
    signals = _fetch(QUERIES, source="noise", label="X")
    seen: set[str] = set()
    rows: list[dict] = []
    for sig in signals:
        if sig.url in seen or len(sig.title) < 40:
            continue
        seen.add(sig.url)
        rows.append(
            {
                "text": sig.title,
                "url": sig.url,
                "author": "",
                "when": sig.published.isoformat() if sig.published else "",
                "likes": "0",
            }
        )
    Path("data").mkdir(exist_ok=True)
    Path("data/x_negatives.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[negatives] {len(rows)} rows -> data/x_negatives.json")
    for row in rows[:5]:
        print("  " + row["text"][:110])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
