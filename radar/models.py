"""Core data model."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING = {
    "ref", "ref_src", "ref_url", "source", "fbclid", "gclid", "igshid",
    "mc_cid", "mc_eid", "spm", "cmpid",
}


def normalize_url(url: str) -> str:
    """Strip tracking noise so the same story dedupes across sources."""
    url = (url or "").strip()
    if not url:
        return ""
    parts = urlsplit(url)
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in _TRACKING
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme, parts.netloc, path, urlencode(query), ""))


def url_hash(url: str) -> str:
    return hashlib.sha1(normalize_url(url).encode("utf-8", "ignore")).hexdigest()[:16]


@dataclass
class Signal:
    title: str
    url: str
    source: str  # x | news | hackernews | reddit | github | mastodon
    topic: str = "general"
    published: datetime | None = None
    summary: str = ""
    engagement: float = 0.0
    score: float = 0.0
    niche_hits: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        return url_hash(self.url)

    @property
    def age_hours(self) -> float:
        if not self.published:
            return 24.0
        now = datetime.now(timezone.utc)
        delta = now - self.published
        return max(0.0, delta.total_seconds() / 3600.0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "topic": self.topic,
            "published": self.published.isoformat() if self.published else None,
            "summary": self.summary,
            "engagement": self.engagement,
            "score": round(self.score, 2),
            "niche_hits": self.niche_hits,
            "meta": self.meta,
        }
