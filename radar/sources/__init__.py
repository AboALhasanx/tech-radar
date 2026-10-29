"""Source registry.

Every fetcher returns list[Signal] and fails soft: one dead source must never
take the whole run down.
"""

from __future__ import annotations

from .. import config
from ..models import Signal
from . import (
    arxiv,
    github_trending,
    google_news,
    hackernews,
    hf_papers,
    mastodon,
    reddit,
    semantic_scholar,
)

__all__ = ["collect_all"]


def collect_all(*, include_x: bool = True, include_news: bool = True) -> list[Signal]:
    signals: list[Signal] = []

    if include_x:
        signals += google_news.fetch_x(config.X_QUERIES)
    if include_news:
        signals += google_news.fetch_news(config.NEWS_QUERIES)

    signals += hackernews.fetch(config.HN_MIN_POINTS)
    signals += reddit.fetch(config.REDDIT_SUBS)
    signals += github_trending.fetch(
        config.GITHUB_MIN_STARS, config.GITHUB_WINDOW_DAYS
    )
    signals += mastodon.fetch(config.MASTODON_TAGS)

    # research lane
    signals += hf_papers.fetch()
    signals += arxiv.fetch(config.ARXIV_FEEDS)
    # Semantic Scholar's keyless pool rate-limits hard (HTTP 429 after the
    # first couple of calls), so it is opt-in rather than default.
    import os

    if os.getenv("S2_ENABLED") == "1":
        signals += semantic_scholar.fetch(config.S2_QUERIES)
    return signals
