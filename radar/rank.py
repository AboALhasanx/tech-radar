"""Clustering and scoring.

The interesting signal is not "a link" but "the same story appearing in
several independent places at once". So we cluster near-duplicate titles and
score the cluster, not the link.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from . import config
from .models import Signal

_WORD_RE = re.compile(r"[a-z0-9\u0600-\u06ff]+", re.IGNORECASE)

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "it", "its", "this", "that",
    "how", "why", "what", "new", "now", "you", "your", "we", "our", "they",
    "from", "at", "by", "as", "has", "have", "will", "can", "not", "just",
    "about", "after", "over", "into", "than", "more", "most", "says", "said",
}

SOURCE_WEIGHT = {
    "x": 1.0,
    "hackernews": 1.0,
    "github": 0.9,
    "news": 0.8,
    "reddit": 0.7,
    "mastodon": 0.6,
}

# A flat "priority" is deliberate: engagement is not comparable across sources
# (HN points, GitHub stars, Mastodon boosts), so it is capped separately and
# source priority only breaks ties.
SOURCE_PRIORITY = {
    "x": 8.0,
    "hackernews": 6.0,
    "github": 5.5,
    "news": 4.5,
    "reddit": 3.5,
    "mastodon": 3.0,
}


def tokens(text: str) -> set[str]:
    words = {w.lower() for w in _WORD_RE.findall(text or "")}
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}


def similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / len(a | b)


@dataclass
class Story:
    lead: Signal
    members: list[Signal] = field(default_factory=list)
    sources: set[str] = field(default_factory=set)
    topics: set[str] = field(default_factory=set)
    score: float = 0.0
    niche_hits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.members:
            self.members = [self.lead]
        self.sources.add(self.lead.source)
        self.topics.add(self.lead.topic)
        self._tokens = tokens(self.lead.title)

    def add(self, signal: Signal) -> None:
        self.members.append(signal)
        self.sources.add(signal.source)
        self.topics.add(signal.topic)
        if signal.engagement > self.lead.engagement:
            self.lead = signal
            self._tokens = tokens(signal.title)

    @property
    def total_engagement(self) -> float:
        return sum(m.engagement for m in self.members)

    @property
    def earliest(self):
        dates = [m.published for m in self.members if m.published]
        return min(dates) if dates else None

    @property
    def age_hours(self) -> float:
        return self.lead.age_hours


def cluster(signals: list[Signal], threshold: float = 0.5) -> list[Story]:
    """Greedy single-pass clustering; order-independent enough for a digest."""
    stories: list[Story] = []
    for signal in signals:
        sig_tokens = tokens(signal.title)
        best: Story | None = None
        best_sim = 0.0
        for story in stories:
            sim = similarity(sig_tokens, story._tokens)
            if sim > best_sim:
                best_sim, best = sim, story
        if best is not None and best_sim >= threshold:
            best.add(signal)
        else:
            stories.append(Story(lead=signal))
    return stories


def score_story(story: Story) -> None:
    age = story.age_hours
    recency = math.exp(-age / config.RECENCY_HALF_LIFE_HOURS) * 40.0

    # Comparable across sources only because it is tightly capped.
    engagement = story.total_engagement
    engagement_score = min(15.0, math.log1p(max(0.0, engagement)) * 2.5)

    # Same story in several places is the real trend signal. A story that
    # matches several X topic queries (ai + agents + opensource) counts too.
    cross = min(
        25.0,
        max(0, len(story.sources) - 1) * 14.0 + max(0, len(story.topics) - 1) * 3.0,
    )

    text = " ".join(m.title + " " + (m.summary or "") for m in story.members).lower()
    hits: list[str] = []
    niche = 0.0
    for term, weight in config.NICHE_TERMS.items():
        if term in text:
            niche += weight * 3.0
            hits.append(term)
    niche = min(config.NICHE_BONUS_CAP, niche)

    priority = max(SOURCE_PRIORITY.get(m.source, 2.0) for m in story.members)
    x_boost = 4.0 if "x" in story.sources else 0.0

    story.niche_hits = sorted(set(hits))
    story.score = round(recency + engagement_score + cross + niche + priority + x_boost, 2)


def rank(signals: list[Signal], top_n: int | None = None) -> list[Story]:
    stories = cluster(signals)
    for story in stories:
        score_story(story)
    stories.sort(key=lambda s: s.score, reverse=True)
    return stories[: (top_n or config.TOP_N)]
