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
sys.path.insert(0, str(ROOT))
from radar import config

CURATED = json.loads((ROOT / "radar" / "curated.json").read_text("utf-8"))

OUT = ["# Sources worth following", "",
       "A curated directory of platforms, newsletters, accounts, and communities.",
       "The scheduled collector reads newsletter feeds from `radar/curated.json`;",
       "the curated X handles feed local refreshes. Platforms are reference links.",
       "Collected communities and search queries are defined in `radar/config.py`.", ""]

OUT += ["## Platforms", "", "| Platform | Why |", "|---|---|"]
for p in CURATED.get("platforms", []):
    OUT.append(f"| [{p['name']}]({p['url']}) | {p['why']} |")

OUT += ["", "## Newsletters", "",
        "Fetched by `radar/sources/newsletters.py` (RSS, free).", "",
        "| Newsletter | Focus | Why |", "|---|---|---|"]
for n in CURATED.get("newsletters", []):
    OUT.append(f"| [{n['name']}]({n['url']}) | `{n['focus']}` | {n['why']} |")

OUT += ["", "## X accounts", "",
        "The local X session searches these curated handles with",
        "`python tools/x_session.py accounts` and saves posts to `data/x_accounts.json`.", "",
        "| Account | Type | Followers | Why |", "|---|---|---|---|"]
for a in CURATED.get("x_accounts", []):
    followers = f"{a['followers']:,}" if a.get("followers") else "—"
    OUT.append(
        f"| `{a['handle']}` | {a.get('category', 'researcher')} | {followers} | {a['why']} |"
    )

OUT += ["", "## Communities", "",
        "Read by the scheduled collectors from `radar/config.py`:", ""]
OUT.append("- Reddit: " + ", ".join(f"r/{s}" for s in config.REDDIT_SUBS))
OUT.append("- Mastodon: " + ", ".join(f"#{t}" for t in config.MASTODON_TAGS))

OUT += ["", "## Adding a source", "",
        "1. Newsletter feeds and X handles: edit `radar/curated.json`; refresh the local X snapshot with `python tools/x_session.py accounts`.",
        "2. Platform reference links: edit `radar/curated.json`.",
        "3. Communities and search queries: edit `radar/config.py`.",
        "4. A new collector needs a fetcher registered in `radar/sources/__init__.py`.",
        "5. Regenerate this page: `python tools/build_sources_doc.py`.", ""]

path = ROOT / "docs" / "SOURCES.md"
path.write_text("\n".join(OUT), encoding="utf-8")
print(f"[docs] wrote {path}")
