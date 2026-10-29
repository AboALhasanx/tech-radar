"""Google News RSS.

Two jobs:
  * `fetch_x`   -> public X posts, because Google News indexes them and
                   exposes the tweet text through RSS (no X API key needed).
  * `fetch_news`-> ordinary coverage for the same topics, so a story that is
                   big on X *and* in the press ranks higher.
"""

from __future__ import annotations

import re
from urllib.parse import quote_plus

from ..feed import parse_feed
from ..http import get
from ..models import Signal

_BASE = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
_SUFFIX_RE = re.compile(r"\s+-\s+[^-]{1,40}$")
_URL_RE = re.compile(r"https?://\S+|\bpic\.x\.com/\S+|\bt\.co/\S+")

# Google News matches loosely, so the query alone lets in reply fragments and
# off-topic chatter ("free agents" in a sports post, "Expo Center" for a trade
# show). A post must clear a strong-signal bar, not just contain the word.
_STRONG = (
    "ai", "artificial intelligence", "llm", "gpt", "claude", "gemini", "openai",
    "anthropic", "deepseek", "qwen", "model", "github", "api", "python", "rust",
    "typescript", "javascript", "flutter", "react native", "rtl", "arabic", "عربي",
    "open source", "open-source", "mcp", "compiler", "benchmark", "kubernetes",
    "docker", "database", "gpu", "linux", "context window", "fine-tun", "inference",
)

_WEAK = (
    "agent", "code", "coding", "developer", "app", "software", "web", "browser",
    "startup", "release", "launch", "expo", "security", "cloud", "server", "framework",
)

_BLOCK = (
    "dodgers", "world series", "nba", "nfl", "premier league", "real estate",
    "expo center", "vacant", "celebrity", "box office", "album", "tour dates",
    "election", "senator", "prime minister",
)

_PROMO = (
    "check out", "sign up", "join us", "register now", "buy now", "limited offer",
    "follow us", "dm me", "link in bio", "start trading", "start earning",
    "mastering ", "deep dive into", "click here",
)


def _hits(terms: tuple[str, ...], low: str) -> int:
    count = 0
    for term in terms:
        if term.isascii() and term.replace("-", "").isalnum() and " " not in term:
            if re.search(rf"\b{re.escape(term)}\b", low):
                count += 1
        elif term in low:
            count += 1
    return count


def looks_like_tech_post(title: str) -> bool:
    low = title.lower().strip()
    if len(low) < 45 or low.startswith("@"):
        return False
    if any(p in low for p in _BLOCK) or any(p in low for p in _PROMO):
        return False
    if re.search(r"\(a\).{0,120}\(b\)", low):  # engagement-bait polls
        return False
    return _hits(_STRONG, low) >= 1 and (_hits(_STRONG, low) * 2 + _hits(_WEAK, low)) >= 2


def _clean_title(title: str, source_name: str) -> str:
    title = (title or "").strip()
    if source_name and title.endswith(f" - {source_name}"):
        title = title[: -(len(source_name) + 3)].strip()
    else:
        title = _SUFFIX_RE.sub("", title).strip()
    # X posts carry t.co / pic.x.com links in the body; they are noise in a headline
    title = _URL_RE.sub("", title)
    return re.sub(r"\s{2,}", " ", title).strip(" -—")


def _fetch(queries: list[tuple[str, str]], source: str, label: str) -> list[Signal]:
    out: list[Signal] = []
    for topic, query in queries:
        url = _BASE.format(q=quote_plus(query))
        try:
            xml_text = get(url, min_gap=2.0)
        except RuntimeError as exc:
            print(f"[google-news] {topic}: {exc}")
            continue

        for item in parse_feed(xml_text):
            title = _clean_title(item["title"], label)
            if source == "x" and not looks_like_tech_post(title):
                continue
            if len(title) < 25:
                continue
            out.append(
                Signal(
                    title=title,
                    url=item["link"],
                    source=source,
                    topic=topic,
                    published=item["published"],
                    summary=item["summary"][:400],
                    meta={"query": query},
                )
            )
    return out


def fetch_x(queries: list[tuple[str, str]]) -> list[Signal]:
    return _fetch(queries, source="x", label="X")


def fetch_news(queries: list[tuple[str, str]]) -> list[Signal]:
    return _fetch(queries, source="news", label="")


def is_x_google_link(url: str) -> bool:
    return "news.google.com" in (url or "")
