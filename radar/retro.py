"""Retrospective mode: what actually trended over the last N days.

X trends are a live-only surface, so a "what happened in the last two months"
question cannot be answered by the trends list. We rebuild it from the archive
Google News keeps of public X posts: sample each week separately, then rank the
terms that keep coming back instead of the ones that spiked once.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

from .config import X_QUERIES
from .feed import parse_feed
from .http import get
from .sources.google_news import _clean_title

_BASE = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"

_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "is",
    "are", "was", "were", "it", "this", "that", "you", "your", "we", "our",
    "they", "from", "at", "by", "as", "has", "have", "will", "can", "not",
    "just", "about", "after", "over", "into", "than", "more", "most", "very",
    "all", "now", "new", "one", "two", "get", "got", "make", "made", "like",
    "what", "when", "how", "why", "who", "its", "it's", "i'm", "i've", "don't",
    "x", "https", "http", "co", "amp",
}

_WORD = re.compile(r"[a-zA-Z][a-zA-Z0-9\-]{2,}")


def _window(days: int, step: int = 7) -> list[tuple[datetime, datetime]]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    windows = []
    cursor = start
    while cursor < end:
        nxt = min(cursor + timedelta(days=step), end)
        windows.append((cursor, nxt))
        cursor = nxt
    return windows


def _fetch_window(start: datetime, end: datetime, query: str) -> list[str]:
    q = f"{query} after:{start:%Y-%m-%d} before:{end:%Y-%m-%d}"
    url = _BASE.format(q=quote_plus(q))
    try:
        xml_text = get(url, min_gap=2.0)
    except RuntimeError as exc:
        print(f"[retro] {start:%Y-%m-%d}: {exc}")
        return []
    return [
        _clean_title(item["title"], "X")
        for item in parse_feed(xml_text)
        if len(item["title"]) > 30
    ]


def _terms(titles: list[str]) -> Counter:
    counter: Counter = Counter()
    for title in titles:
        for word in _WORD.findall(title.lower()):
            if word not in _STOP and len(word) > 3:
                counter[word] += 1
    return counter


def retro_report(days: int = 60, *, out_dir: str = "digest") -> Path:
    windows = _window(days)
    print(f"[retro] {len(windows)} weekly windows over {days} days")

    per_window: list[tuple[str, list[str]]] = []
    for start, end in windows:
        titles: list[str] = []
        for _topic, query in X_QUERIES:
            # strip the freshness operator; the date range replaces it
            base = re.sub(r"\s*when:\S+", "", query)
            titles += _fetch_window(start, end, base)
        label = f"{start:%Y-%m-%d} → {end:%Y-%m-%d}"
        print(f"[retro] {label}: {len(titles)} posts")
        per_window.append((label, titles))

    # terms that appear in many windows are the real trend; one-week spikes are noise
    window_hits: dict[str, int] = defaultdict(int)
    total: Counter = Counter()
    for _label, titles in per_window:
        terms = _terms(titles)
        for term, count in terms.items():
            if count >= 3:
                window_hits[term] += 1
                total[term] += count

    ranked = sorted(
        total.items(),
        key=lambda kv: (window_hits[kv[0]], kv[1]),
        reverse=True,
    )[:40]

    now = datetime.now(timezone.utc)
    out = [
        f"# تحليل رجعي — آخر {days} يوم على X",
        "",
        f"> {len(per_window)} نوافذ أسبوعية · {sum(len(t) for _, t in per_window)} منشور",
        "",
        "## المصطلحات الأثبت (ظهرت بأسابيع متعددة)",
        "",
        "| المصطلح | أسابيع | تكرار |",
        "|---|---|---|",
    ]
    for term, count in ranked:
        out.append(f"| `{term}` | {window_hits[term]} | {count} |")

    out += ["", "## عيّنات لكل أسبوع", ""]
    for label, titles in per_window:
        out += [f"### {label}", ""]
        for title in titles[:5]:
            out.append(f"- {title[:180]}")
        out.append("")

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / f"retro-{now:%Y-%m-%d}.md"
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"[retro] wrote {path}")
    return path
