"""Configuration for tech-radar.

Everything here is data, not code: swap queries and weights without touching
the pipeline. Sources are all free and keyless by default.
"""

from __future__ import annotations

# ---------------------------------------------------------------- X (via Google News)
# Google News indexes public X posts and exposes them through RSS, which gives
# us real tweet text without the X API. `when:` keeps the window fresh.
X_QUERIES: list[tuple[str, str]] = [
    ("ai", 'site:x.com (AI OR LLM OR "language model" OR OpenAI OR Anthropic) when:2d'),
    ("agents", 'site:x.com (agent OR agents OR agentic OR MCP) when:2d'),
    ("opensource", 'site:x.com ("open source" OR "open-source" OR GitHub) when:2d'),
    ("devtools", 'site:x.com (developer OR coding OR IDE OR compiler) when:2d'),
    ("arabic", 'site:x.com (Arabic OR RTL OR عربي OR "الذكاء الاصطناعي") when:7d'),
    ("mobile", 'site:x.com (Flutter OR "React Native" OR Expo OR Android) when:7d'),
]

# ---------------------------------------------------------------- general news
NEWS_QUERIES: list[tuple[str, str]] = [
    ("ai", "artificial intelligence OR LLM when:2d"),
    ("dev", "open source OR developer tools when:2d"),
    ("hardware", "chip OR GPU OR semiconductor when:3d"),
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

RECENCY_HALF_LIFE_HOURS = 18.0
CROSS_SOURCE_BONUS = 14.0  # points per extra independent source
NICHE_BONUS_CAP = 20.0

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
