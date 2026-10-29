# Sources worth following

A curated map of where research tooling news actually appears. The radar
reads the machine-readable entries automatically; the X accounts are for
you to follow, and for the local scraper when you are at the machine.

## Platforms

| Platform | Why |
|---|---|
| [alphaXiv / OpenResearch](https://www.alphaxiv.org) | paper discussion plus an open research-agent app |
| [Hugging Face Papers](https://huggingface.co/papers) | daily papers with code and discussion |
| [Semantic Scholar](https://www.semanticscholar.org) | the reference graph researchers actually query |
| [Connected Papers](https://www.connectedpapers.com) | visual literature mapping |
| [Elicit](https://elicit.com) | structured literature review |
| [Consensus](https://consensus.app) | claim-level answers from papers |
| [SciSpace](https://scispace.com) | read, annotate and explain papers |
| [Undermind](https://www.undermind.ai) | deep literature search |
| [NotebookLM](https://notebooklm.google.com) | source-grounded notes and audio overviews |
| [Zotero](https://www.zotero.org) | reference manager with a plugin ecosystem |
| [Overleaf](https://www.overleaf.com) | collaborative LaTeX |
| [Typst](https://typst.app) | fast modern typesetting, strong RTL story |
| [OpenReview](https://openreview.net) | peer review in the open |
| [ResearchRabbit](https://www.researchrabbit.ai) | citation-network discovery |
| [Litmaps](https://www.litmaps.com) | literature maps that update |
| [Papers with Code](https://paperswithcode.com) | benchmarks and implementations |

## Newsletters

Fetched by `radar/sources/newsletters.py` (RSS, free).

| Newsletter | Focus | Why |
|---|---|---|
| [Import AI](https://importai.substack.com/feed) | `research` | Jack Clark's weekly policy + research briefing; the closest thing to a research weather report. |
| [Interconnects](https://www.interconnects.ai/feed) | `research` | Nathan Lambert on post-training, evals and open models — the technical layer under research tooling. |
| [Ahead of AI](https://magazine.sebastianraschka.com/feed) | `research` | Sebastian Raschka's long-form explanations of new architectures and training methods. |
| [One Useful Thing](https://www.oneusefulthing.org/feed) | `research_tools` | Ethan Mollick on how researchers and students actually use these tools day to day. |
| [The Gradient](https://thegradient.pub/rss/) | `research` | Research commentary and interviews from people inside the field. |

## X accounts

Follow these; the local scraper can pull their timelines with
`python tools/x_session.py accounts` once they are in your following list.

| Account | Type | Followers | Why |
|---|---|---|---|
| `@TheRundownAI` | aggregator | 230,801 | Daily AI news roundup, 2M+ newsletter readers — the widest net |
| `@AIHighlight` | aggregator | 626,250 | Curates the day's AI and tech posts; highest reach in the list |
| `@HeyBarsee` | aggregator | 268,281 | Daily AI/tech developments and tool finds |
| `@aibreakfast` | aggregator | 242,740 | Rumors and launches, earlier than the press |
| `@mreflow` | aggregator | 121,538 | Matt Wolfe — FutureTools database and weekly tool roundups |
| `@bentossell` | aggregator | 202,588 | Ben's Bites — dev tools and infra, builder lens |
| `@DeepLearningAI` | aggregator | 355,664 | Andrew Ng's team: courses, The Batch, applied AI news |
| `@ArtificialAnlys` | aggregator | 172,634 | Independent model benchmarks and price/performance analysis |
| `@toolfolio` | aggregator | 18,217 | Tool discovery feed, high signal per post |
| `@paperswithcode` | aggregator | 112,651 | Benchmarks and implementations behind new papers |
| `@aidailybrief` | aggregator | 5,035 | The AI Daily Brief podcast — one short daily analysis |
| `@TheTuringPost` | aggregator | 89,084 | Research explainers and tool roundups, strong on System-1 |
| `@askalphaxiv` | researcher | — | alphaXiv / OpenResearch — turns coding agents into research agents |
| `@_akhaliq` | researcher | — | fastest paper-to-tweet account in the field |
| `@omarsar0` | researcher | 326,665 | DAIR.AI — research summaries and tooling |
| `@cwolferesearch` | researcher | 42,760 | research paper walkthroughs and study notes |
| `@emollick` | researcher | — | how academics actually adopt AI |
| `@owainevans_uk` | researcher | — | AI and academic assessment, education policy |
| `@_jasonwei` | researcher | — | reasoning and post-training research |
| `@drjimfan` | researcher | — | embodied AI and research practice |
| `@karpathy` | researcher | — | teaching and building, rarely but densely |
| `@huggingface` | lab | — | models, papers and tooling, first |
| `@allen_ai` | lab | — | Ai2: Semantic Scholar, OLMo, research tooling |
| `@OpenReview` | lab | — | peer review and venue announcements |
| `@arxiv` | lab | — | official arXiv announcements |
| `@zotero` | tool | — | reference management releases |
| `@overleaf` | tool | — | LaTeX collaboration releases |
| `@typst` | tool | — | the modern typesetting alternative |

## Communities

Subreddits and Mastodon tags the radar already reads:

- Reddit: r/AskAcademia, r/PhD, r/GradSchool, r/MachineLearning, r/LocalLLaMA, r/academia
- Mastodon: #academicchatter, #openscience, #phd, #research

## Adding a source

1. Newsletters and platforms: edit `radar/curated.json`.
2. Communities: edit `REDDIT_SUBS` / `MASTODON_TAGS` in `radar/config.py`.
3. Queries: edit `X_QUERIES` / `NEWS_QUERIES` in `radar/config.py`.
4. Regenerate this page: `python tools/build_sources_doc.py`.
