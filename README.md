# tech-radar

Free, keyless discovery of what is actually moving in tech — built to answer one
question every morning: **what should I look at today?**

No X API key. No paid news API. No server. It runs on a stock Python install and
a GitHub Actions cron.

```bash
python main.py            # collect → rank → digest/2026-10-29.md
python main.py --publish  # also send the top stories to Telegram
python main.py --retro 60 # what trended over the last two months
```

---

## The trick: X without the X API

X's API is expensive and its trends endpoint is live-only. But Google News
indexes public X posts and serves them through plain RSS:

```
https://news.google.com/rss/search?q=site:x.com+(AI+OR+LLM)+when:2d
```

That returns real tweet text, timestamps, and links — free, keyless, and stable
enough to run unattended. The radar leans on it, then cross-checks every story
against independent sources so a single loud account cannot dominate the digest.

When you want the *personal* view (your own following list, your own timeline),
`tools/x_session.py` drives the Chromium you are already logged into — locally
only, nothing leaves the machine.

## Sources

| Source | How | Cost | What it adds |
|---|---|---|---|
| X posts | Google News `site:x.com` | free | the primary signal |
| X (personal) | Playwright + your profile | free, local | your following list and timeline |
| Hacker News | Algolia API | free | builder-grade filtering |
| GitHub | search API (new + starred) | free | what people are actually shipping |
| Reddit | public Atom feeds | free | practitioner chatter |
| Mastodon | public API | free | early, non-algorithmic chatter |
| Press | Google News RSS | free | confirmation, not discovery |

## How ranking works

A link is not a story. Titles are clustered (token Jaccard ≥ 0.5), then the
cluster is scored:

- **recency** — exponential decay, 18 h half-life
- **cross-source** — the same story in X *and* HN *and* press is the real trend
- **topic spread** — matches several X queries (ai + agents + open source)
- **niche** — Arabic, RTL, local-first, agents, the stacks used here
- **engagement** — capped, because HN points and GitHub stars are not comparable

Engagement is deliberately capped at 15 points. Without that cap, Hacker News
swallows the digest and X — the reason the tool exists — never surfaces.

## Output

```
digest/2026-10-29.md   human-readable, Arabic, RTL-friendly
data/latest.json       machine-readable feed for agents
data/radar.db          what has already been shown (SQLite)
```

`latest.json` is the integration point: point any agent at it and it can answer
"what changed since yesterday" without re-fetching the web.

## Running it unattended

`.github/workflows/radar.yml` runs every six hours, commits the digest, and
optionally posts to Telegram. Add `GROQ_API_KEY` for Arabic summaries and
`TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHANNEL_ID` for delivery. Neither is required.

## Retrospective mode

`--retro 60` samples the last two months in weekly windows and ranks terms by
**how many weeks they appear in**, not by raw frequency. A one-week spike is
noise; a term that shows up in seven windows is a trend.

## Tests

```bash
python -m pytest tests -q
```

Eleven unit tests cover feed parsing, URL normalisation, clustering and scoring.
No network access required.

## Limits, stated plainly

- Google News indexing is a sample of X, not a firehose. Viral posts that never
  get indexed will not appear.
- No like/repost counts on the X side, so ranking relies on recency and
  cross-source confirmation instead.
- `tools/x_session.py` copies the cookie jar to a throwaway profile and never
  writes back to the real one. It is a local convenience, not a scraper to run
  at scale.
- Reddit's RSS endpoints rate-limit aggressively; the source fails soft.

## License

MIT.
