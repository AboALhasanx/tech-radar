"""Configuration for tech-radar.

Everything here is data, not code: swap queries and weights without touching
the pipeline. Sources are all free and keyless by default.
"""

from __future__ import annotations

# ---------------------------------------------------------------- X (via Google News)
# Google News indexes public X posts and exposes them through RSS, which gives
# us real tweet text without the X API. `when:` keeps the window fresh.
X_QUERIES: list[tuple[str, str]] = [
    ("ai", 'site:x.com (AI OR LLM OR "language model" OR OpenAI OR Anthropic) when:3d'),
    ("agents", 'site:x.com (agent OR agents OR agentic OR MCP) when:3d'),
    ("opensource", 'site:x.com ("open source" OR "open-source" OR "self-hosted") when:3d'),
    ("devtools", 'site:x.com (developer OR coding OR IDE OR compiler) when:3d'),
    # the academic lane: tools researchers actually use, not papers
    ("research_tools", 'site:x.com (Elicit OR Consensus OR SciSpace OR NotebookLM OR Zotero OR Overleaf OR "literature review") when:14d'),
    ("harness", 'site:x.com (harness OR "coding agent" OR skill OR "agent skills") when:3d'),
    # free tiers, credits, trials, open alternatives
    ("free", 'site:x.com ("free tier" OR "free credits" OR "free trial" OR "no API key" OR "free plan") when:7d'),
    ("launch", 'site:x.com ("open source alternative" OR "just launched" OR "now available" OR "v1.0") when:3d'),
    ("arabic", 'site:x.com (Arabic OR RTL OR عربي OR "الذكاء الاصطناعي") when:7d'),
    ("mobile", 'site:x.com (Flutter OR "React Native" OR Expo OR Android) when:7d'),
]

# ---------------------------------------------------------------- general news
NEWS_QUERIES: list[tuple[str, str]] = [
    ("ai", "artificial intelligence OR LLM when:3d"),
    ("dev", "open source OR developer tools when:3d"),
    ("hardware", "chip OR GPU OR semiconductor when:3d"),
    ("tools", "AI tool launch OR productivity software when:7d"),
    ("free", '"free tier" OR "free plan" OR "open source alternative" when:7d'),
]

# ---------------------------------------------------------------- community
REDDIT_SUBS = [
    "technology",
    "LocalLLaMA",
    "programming",
    "MachineLearning",
    "FlutterDev",
    "Arabic",
]

MASTODON_TAGS = ["ai", "opensource", "programming"]

HN_MIN_POINTS = 80
GITHUB_MIN_STARS = 40
GITHUB_WINDOW_DAYS = 7

# ---------------------------------------------------------------- research
# The academic lane: papers, research harnesses, AI-assisted writing.
S2_QUERIES: list[tuple[str, str]] = [
    # research workflow tools, not papers about research
    ("research_tools", "AI literature review tool"),
    ("research_tools", "academic writing assistant"),
    ("harness", "research agent workflow"),
    ("arabic", "Arabic natural language processing"),
    ("ocr", "document understanding OCR"),
]

ARXIV_FEEDS = [
    ("cs.CL", "https://rss.arxiv.org/rss/cs.CL"),
    ("cs.AI", "https://rss.arxiv.org/rss/cs.AI"),
    ("cs.HC", "https://rss.arxiv.org/rss/cs.HC"),
]

# The academic lane is about tooling, so these topics get the ranking boost.
RESEARCH_TOPICS = {"research_tools", "harness", "free", "launch", "writing"}
RESEARCH_BOOST = 8.0

# ---------------------------------------------------------------- ranking
# Terms that matter for this profile: Arabic-first interfaces, RTL, local-first
# software, agents, and the stacks actually used here.
NICHE_TERMS: dict[str, float] = {
    "arabic": 1.6,
    "rtl": 1.6,
    "bidi": 1.4,
    "عربي": 1.6,
    "العربية": 1.4,
    "local-first": 1.3,
    "offline": 0.8,
    "on-device": 0.9,
    "agent": 0.8,
    "mcp": 0.8,
    "flutter": 0.7,
    "expo": 0.7,
    "python": 0.4,
    "typescript": 0.4,
    "open source": 0.6,
    "local": 0.3,
}

RECENCY_HALF_LIFE_HOURS = 24.0
CROSS_SOURCE_BONUS = 14.0  # points per extra independent source
NICHE_BONUS_CAP = 20.0
# No single source may take more than this share of the digest.
MAX_SOURCE_SHARE = 0.4

# ---------------------------------------------------------------- taste model
# Trained from the account's own likes (radar/ml). When the export is missing
# the radar simply runs without it.
TASTE_MODEL_PATH = "data/taste_model.json"
TASTE_MIN_PROB = 0.15  # hard floor for X items
TASTE_WEIGHT = 40.0  # (p - 0.5) * weight, so the range is -20..+20

# ---------------------------------------------------------------- persistence
SEEN_PATH = "data/seen.json"
ARCHIVE_KEEP_MONTHS = 12

# ---------------------------------------------------------------- output
TOP_N = 15
DIGEST_DIR = "digest"
DATA_DIR = "data"
DB_PATH = "data/radar.db"

REQUEST_TIMEOUT = 20
SLEEP_BETWEEN_REQUESTS = 1.5
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 tech-radar/1.0"
)
