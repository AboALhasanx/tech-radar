"""Source registry.

Every fetcher returns list[Signal] and fails soft: one dead source must never
take the whole run down.
"""

from __future__ import annotations

from .. import config
from ..models import Signal
from . import (
    arxiv,
    github_tools,
    github_trending,
    google_news,
    hackernews,
    hf_papers,
    mastodon,
    newsletters,
    producthunt,
    reddit,
    semantic_scholar,
    x_accounts,
)

__all__ = ["collect_all"]


def collect_all(*, include_x: bool = True, include_news: bool = True) -> list[Signal]:
    import os

    signals: list[Signal] = []

    if include_x:
        signals += google_news.fetch_x(config.X_QUERIES)
    # curated researcher accounts, refreshed locally
    signals += x_accounts.fetch()
    if include_news:
        signals += google_news.fetch_news(config.NEWS_QUERIES)

    signals += hackernews.fetch(config.HN_MIN_POINTS)
    signals += reddit.fetch(config.REDDIT_SUBS)
    signals += github_trending.fetch(
        config.GITHUB_MIN_STARS, config.GITHUB_WINDOW_DAYS
    )
    signals += github_tools.fetch()
    signals += producthunt.fetch()
    signals += newsletters.fetch()
    signals += mastodon.fetch(config.MASTODON_TAGS)

    # Papers are opt-in: the point of this radar is the tooling around
    # research, not the papers themselves.
    if os.getenv("PAPERS_ENABLED") == "1":
        signals += hf_papers.fetch()
        signals += arxiv.fetch(config.ARXIV_FEEDS)
        signals += semantic_scholar.fetch(config.S2_QUERIES)
    return signals
