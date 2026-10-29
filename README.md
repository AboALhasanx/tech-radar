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
| Product Hunt | public RSS | free | launches before the press |
| Newsletters | curated RSS | free | Import AI, Interconnects, Ahead of AI, One Useful Thing |
| GitHub tooling | topic search API | free | research tools people actually install |
| Hacker News | Algolia API | free | builder-grade filtering |
| GitHub | search API (new + starred) | free | what people are actually shipping |
| Reddit | public Atom feeds | free | practitioner chatter |
| Mastodon | public API | free | early, non-algorithmic chatter |
| Press | Google News RSS | free | confirmation, not discovery |

## Tooling lane

This is not a papers feed. The academic side tracks the **tools around the
work** — the thing a researcher installs, pays for, or gets for free:

| Lane | What it tracks |
|---|---|
| `research_tools` | literature review, reference managers, Zotero/Overleaf/Typst, research workbenches |
| `harness` | agent harnesses, skills, MCP servers, research agents |
| `free` | free tiers, credits, trials, "no API key", open-source alternatives |
| `launch` | new products and v1.0 releases before they reach the press |

These four are ranked first and carry an 8-point boost. Papers still exist as
an opt-in (`PAPERS_ENABLED=1`) but they are not the point.

**The full directory — platforms, newsletters, X accounts, communities — is in
[`docs/SOURCES.md`](docs/SOURCES.md).** It is generated from
`radar/curated.json`, so adding a source is a one-line edit.

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

## Taste model — learned from your own likes

The radar can rank by *your* taste instead of a generic notion of importance.
`radar/ml` trains a linear model on the posts you actually liked:

```bash
python tools/x_session.py likes     # pull your likes through the local session
python tools/collect_negatives.py   # easy negatives (sports, celebrity, politics)
python -m radar.ml.train            # fit + evaluate + export
```

Model:

```
p(liked | post) = sigmoid( w · tfidf(post) + u · shape(post) + b )
```

- **tf-idf** — sublinear `1 + log(tf)`, smoothed `log((1+N)/(1+df)) + 1`, L2 norm
- **shape** — structural signals (code fences, version numbers, benchmarks, links)
- **logistic regression** — balanced class weights, because likes are a minority
- **fit on 80%, evaluated on 20%**, plus 5-fold cross-validation

Reference run on 1,690 examples (682 liked, 1,008 not):

| metric | value |
|---|---|
| ROC-AUC | 0.860 |
| Average precision | 0.804 |
| Precision@20 | 1.000 |
| 5-fold AUC | 0.813 ± 0.015 |

Inference is pure Python: the export is a term→weight table, and a parity test
confirms it matches scikit-learn to 2e-16. A tweet is dropped from the digest
when `p < 0.15`; every story shows its match score.

## Output

```
digest/brief-2026-10-29.md   the 3-day brief (primary artifact)
digest/weekly/2026-W44.md    the weekly rollup
CATCHUP.md                   rolling 30-day picture, always current
data/brief.json              machine-readable feed for agents
data/archive/2026-10.jsonl.gz durable history
site/index.html + feed.xml   static site and RSS for GitHub Pages
```

`latest.json` is the integration point: point any agent at it and it can answer
"what changed since yesterday" without re-fetching the web.

## Running it unattended

`radar.yml` runs **every three days** and a weekly rollup on Sundays, commits
the brief and the archive, builds the static site, and deploys it to GitHub
Pages:

```
https://aboalhasanx.github.io/tech-radar/          site
https://aboalhasanx.github.io/tech-radar/feed.xml   RSS
```

All free for a public repository: Actions is the runner, Pages is the host,
and there is no server to pay for. ntfy (`NTFY_TOPIC`) and Telegram
(`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ID`) are optional push channels;
`GROQ_API_KEY` enables Arabic summaries. None are required.

## If you disappear for two months

The radar is built for absence, not for live monitoring:

- every run archives the top 60 stories to `data/archive/YYYY-MM.jsonl.gz`
- a Sunday job writes `digest/weekly/2026-W44.md` and refreshes **`CATCHUP.md`**
- `CATCHUP.md` ranks by **longevity** — how many separate days a story kept
  surfacing — so a three-week thread everyone kept talking about beats a
  one-day spike
- `radar/watchlist.json` decides what is worth a Telegram ping while you are away

Read `docs/RETURNING.md` for the exact list of what to open first.

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
