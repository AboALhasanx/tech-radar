"""Generate docs/SOURCES.md from radar/curated.json (single source of truth)."""

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

OUT = ["# Sources worth following", "",
       "A curated map of where research tooling news actually appears. The radar",
       "reads the machine-readable entries automatically; the X accounts are for",
       "you to follow, and for the local scraper when you are at the machine.", ""]

OUT += ["## Platforms", "", "| Platform | Why |", "|---|---|"]
for p in CURATED.get("platforms", []):
    OUT.append(f"| [{p['name']}]({p['url']}) | {p['why']} |")

OUT += ["", "## Newsletters", "",
        "Fetched by `radar/sources/newsletters.py` (RSS, free).", "",
        "| Newsletter | Focus | Why |", "|---|---|---|"]
for n in CURATED.get("newsletters", []):
    OUT.append(f"| [{n['name']}]({n['url']}) | `{n['focus']}` | {n['why']} |")

OUT += ["", "## X accounts", "",
        "Follow these; the local scraper can pull their timelines with",
        "`python tools/x_session.py history` once they are in your following list.", "",
        "| Account | Why |", "|---|---|"]
for a in CURATED.get("x_accounts", []):
    OUT.append(f"| `{a['handle']}` | {a['why']} |")

OUT += ["", "## Communities", "",
        "Subreddits and Mastodon tags the radar already reads:", ""]
OUT.append("- Reddit: " + ", ".join(f"r/{s}" for s in CURATED.get("subreddits", [])))
OUT.append("- Mastodon: " + ", ".join(f"#{t}" for t in CURATED.get("mastodon_tags", [])))

OUT += ["", "## Adding a source", "",
        "1. Newsletters and platforms: edit `radar/curated.json`.",
        "2. Communities: edit `REDDIT_SUBS` / `MASTODON_TAGS` in `radar/config.py`.",
        "3. Queries: edit `X_QUERIES` / `NEWS_QUERIES` in `radar/config.py`.",
        "4. Regenerate this page: `python tools/build_sources_doc.py`.", ""]

path = ROOT / "docs" / "SOURCES.md"
path.write_text("\n".join(OUT), encoding="utf-8")
print(f"[docs] wrote {path}")
