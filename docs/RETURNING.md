# When you come back

You will be away. This file is the contract for what the radar does in the
meantime, and what to read first when you return.

## What runs without you

| When | What | Where it lands |
|---|---|---|
| every 3 days, 06:00 UTC | collect, filter through the taste model, archive, publish a 3-day brief, ping ntfy/Telegram only on watchlist matches | `digest/brief-YYYY-MM-DD.md` |
| Sunday 06:00 UTC | weekly rollup + refresh the rolling brief | `digest/weekly/YYYY-Www.md`, `CATCHUP.md` |
| every deploy | static site + RSS | `https://aboalhasanx.github.io/tech-radar/` |

The scheduled workflow commits its own output, which also keeps GitHub from
disabling the schedule after 60 days of repository inactivity.

## Three ways to receive it, all free

1. **RSS** — subscribe to `https://aboalhasanx.github.io/tech-radar/feed.xml`
   in any reader (Feedly, Inoreader, NetNewsWire, Thunderbird). Nothing to host.
2. **ntfy** — install the ntfy app, subscribe to your topic. Set the repository
   secret `NTFY_TOPIC` (no account needed). Alerts and the weekly summary arrive
   as push notifications.
3. **Telegram** — optional, same as before: `TELEGRAM_BOT_TOKEN` +
   `TELEGRAM_CHANNEL_ID` secrets.

If none are configured, the repo itself is the inbox: open `CATCHUP.md`.

## Read these three, in this order

1. **`CATCHUP.md`** — the rolling 30-day picture. Ranked by how many separate
   days a story kept surfacing, not by freshness.
2. **`digest/weekly/`** — one file per week. Away two months? Read the newest
   two and skim the rest.
3. **`digest/brief-*.md`** — the 3-day detail, only when a specific window matters.

## Commands, when you want more

```bash
python main.py --catchup 60        # two months, re-ranked from the archive
python main.py --every 3           # collect + 3-day brief now
python main.py --weekly            # rebuild this week + CATCHUP.md now
python main.py --retro 60          # X-only retrospective (what trended)
python tools/archive_stats.py 30   # what is actually in the archive
```

## Tuning while away

`radar/watchlist.json` holds the keywords worth interrupting you for. Edit it
in the GitHub web UI; the next run picks it up. `radar/config.py` holds the
queries per lane (research, writing, reasoning, learning, arabic, mobile).

## If the schedule stops

GitHub disables scheduled workflows after 60 days without repository activity.
The bot commits on every run, so this should not happen — but if the Actions
tab shows the workflow disabled, open it and press **Enable workflow**.

The archive is the only irreplaceable piece. It lives in `data/archive/` as one
gzip JSONL per month and is committed on every run.
