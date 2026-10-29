# When you come back

You will be away. This file is the contract for what the radar does in the
meantime, and what to read first when you return.

## What runs without you

| When | What | Where it lands |
|---|---|---|
| every 6 hours | collect sources, filter through the taste model, archive the top 60, ping Telegram only on watchlist matches | `digest/YYYY-MM-DD.md`, `data/archive/` |
| Sunday 06:00 UTC | weekly rollup + refresh the rolling brief | `digest/weekly/YYYY-Www.md`, `CATCHUP.md` |
| on demand | a brief for any window | `python main.py --catchup 30` |

The scheduled workflow commits its own output, which also keeps GitHub from
disabling the schedule after 60 days of repository inactivity.

## Read these three, in this order

1. **`CATCHUP.md`** — the rolling 30-day picture. Thirty stories, ranked by how
   many separate days they kept surfacing, not by how fresh they are.
2. **`digest/weekly/`** — one file per week. If you were away two months, that
   is eight files; read the newest two and skim the rest.
3. **`digest/`** — daily detail, only when a specific day matters.

## Commands, when you want more

```bash
python main.py --catchup 60        # two months, re-ranked from the archive
python main.py --weekly            # rebuild this week + CATCHUP.md now
python main.py --retro 60          # X-only retrospective (what trended)
python tools/theme_scan.py        # mine the archive by theme
python tools/show_latest.py        # what the last run produced
```

## Tuning while away

`radar/watchlist.json` holds the keywords worth interrupting you for. Edit it
in the GitHub web UI and the next run picks it up:

```json
{
  "min_score": 50,
  "keywords": ["jev", "ocr", "expo", "rtl", "mcp"]
}
```

Alerts go to Telegram only when `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID`
are set as repository secrets. Without them, matches are printed in the run
log and still appear in the digest.

## If the schedule stops

GitHub disables scheduled workflows after 60 days without repository activity.
The bot commits on every run, so this should not happen — but if the Actions
tab shows the workflow disabled, open it and press **Enable workflow**.

The archive is the only irreplaceable piece. It lives in `data/archive/` as one
gzip JSONL per month and is committed on every run.
