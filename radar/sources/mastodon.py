"""Mastodon hashtag timelines — free, keyless, and often ahead of the press."""

from __future__ import annotations

from ..feed import parse_date, strip_html
from ..http import get_json
from ..models import Signal

_URL = "https://mastodon.social/api/v1/timelines/tag/{tag}?limit=20"


def fetch(tags: list[str]) -> list[Signal]:
    out: list[Signal] = []
    for tag in tags:
        try:
            posts = get_json(_URL.format(tag=tag), min_gap=1.5)
        except RuntimeError as exc:
            print(f"[mastodon] #{tag}: {exc}")
            continue

        for post in posts:
            text = strip_html(post.get("content") or "")
            if len(text) < 40:
                continue
            # first sentence reads better than a raw truncation
            first = text.split(". ")[0]
            title = first if 40 <= len(first) <= 150 else text[:140].rsplit(" ", 1)[0] + "…"
            out.append(
                Signal(
                    title=title,
                    url=post.get("url") or "",
                    source="mastodon",
                    topic="community",
                    published=parse_date(post.get("created_at")),
                    summary=text[:400],
                    engagement=float(
                        (post.get("favourites_count") or 0)
                        + (post.get("reblogs_count") or 0) * 2
                    ),
                    meta={"account": (post.get("account") or {}).get("acct", "")},
                )
            )
    return out
