"""Catch-up mode: what happened while you were not looking.

Daily digests answer "what is new today". This answers the question a person
returning after three weeks actually asks: "what mattered, and what kept
coming back?" So the ranking is by **longevity** — how many separate days a
story surfaced — not by how fresh it is.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import archive, config
from .rank import similarity, tokens
from .render import SOURCE_LABEL, TOPIC_LABEL

TOPIC_ORDER = [
    "research_tools", "harness", "free", "launch", "writing", "reasoning",
    "learning", "ai", "agents", "opensource", "devtools", "code", "mobile",
    "arabic", "hardware", "community", "dev", "general",
]


@dataclass
class Item:
    title: str
    url: str
    story_id: str = ""
    topic: str = "general"
    sources: set[str] = field(default_factory=set)
    topics: set[str] = field(default_factory=set)
    days: set[str] = field(default_factory=set)
    max_score: float = 0.0
    taste: float = 0.0
    title_ar: str = ""
    ar: str = ""
    meta: dict = field(default_factory=dict)
    _tokens: set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "id": self.story_id,
            "title": self.title,
            "title_ar": self.title_ar,
            "url": self.url,
            "topic": self.topic,
            "sources": sorted(self.sources),
            "topics": sorted(self.topics),
            "days": len(self.days),
            "score": round(self.rank_score, 2),
            "taste": self.taste,
            "ar": self.ar,
            "meta": self.meta,
        }

    def add(self, row: dict) -> None:
        if row.get("id") and not self.story_id:
            self.story_id = str(row["id"])
        self.sources.update(row.get("sources") or [])
        self.topics.update(row.get("topics") or [])
        day = (row.get("saved_at") or "")[:10]
        if day:
            self.days.add(day)
        if row.get("score", 0) > self.max_score:
            self.max_score = float(row["score"])
            self.title = row.get("title") or self.title
            self.url = row.get("url") or self.url
            self.topic = row.get("topic") or self.topic
            self.meta = row.get("meta") or {}
            self._tokens = tokens(self.title)
        self.taste = max(self.taste, float(row.get("taste") or 0))
        if row.get("title_ar"):
            self.title_ar = row["title_ar"]
        if row.get("ar"):
            self.ar = row["ar"]

    @property
    def longevity(self) -> float:
        # a story seen on 4 separate days beats a one-day spike
        return self.max_score * (1.0 + 0.35 * math.log1p(len(self.days)))

    @property
    def rank_score(self) -> float:
        cross = 6.0 * max(0, len(self.sources) - 1)
        research = (
            config.RESEARCH_BOOST
            if (self.topics | {self.topic}) & config.RESEARCH_TOPICS
            else 0.0
        )
        taste = self.taste
        if "paper" in self.sources and taste < 0.5:
            taste = 0.5
        newsletter = 6.0 if "newsletter" in self.sources else 0.0
        return self.longevity + cross + research + newsletter + (taste - 0.5) * 20


def _cluster(rows: list[dict], threshold: float = 0.5) -> list[Item]:
    items: list[Item] = []
    for row in rows:
        title = row.get("title") or ""
        if not title:
            continue
        sig = tokens(title)
        best: Item | None = None
        best_sim = 0.0
        for item in items:
            sim = similarity(sig, item._tokens)
            if sim > best_sim:
                best_sim, best = sim, item
        if best is not None and best_sim >= threshold:
            best.add(row)
        else:
            item = Item(
                title=title,
                url=row.get("url") or "",
                story_id=str(row.get("id") or ""),
                topic=row.get("topic") or "general",
                max_score=float(row.get("score") or 0),
                taste=float(row.get("taste") or 0),
                title_ar=row.get("title_ar") or "",
                ar=row.get("ar") or "",
                meta=row.get("meta") or {},
                _tokens=sig,
            )
            item.add(row)
            items.append(item)
    return items


def load_items(days: int = 30) -> list[Item]:
    rows = archive.load_range(days)
    items = _cluster(rows)
    items.sort(key=lambda i: i.rank_score, reverse=True)
    return items


def _period_line(days: int) -> str:
    now = datetime.now(timezone.utc)
    return f"آخر {days} يوم — حتى {now:%Y-%m-%d}"


def render_report(days: int = 30, top: int = 25, headline: str = "") -> str:
    items = load_items(days)
    if not items:
        return (
            f"# ما فاتك — {_period_line(days)}\n\n"
            "> الأرشيف فاضي بعد. الرادار يحتاج كم يوم تشغيل حتى يجمع بيانات.\n"
        )

    by_topic: dict[str, list[Item]] = {}
    for item in items:
        key = item.topic if item.topic in TOPIC_LABEL else "general"
        by_topic.setdefault(key, []).append(item)

    total_days = len({d for item in items for d in item.days})
    out = [
        f"# ما فاتك — {_period_line(days)}",
        "",
        f"> **{len(items)}** قصة من **{total_days}** يوم تغطية · مرتبة بـ**طول البقاء** مو بالحداثة",
        "",
    ]

    if headline:
        out += ["## الخلاصة", "", headline.strip(), ""]

    out += ["## الأهم", ""]
    for i, item in enumerate(items[:top], 1):
        out.append(f"### {i}. {item.title_ar or item.title}")
        out.append("")
        if item.title_ar and item.title_ar != item.title:
            out.append(f"**العنوان الأصلي:** {item.title}")
            out.append("")
        if item.ar:
            out.append(item.ar)
            out.append("")
        sources = " · ".join(SOURCE_LABEL.get(s, s) for s in sorted(item.sources))
        days_seen = len(item.days)
        out.append(
            f"- **المصادر:** {sources} · **ظهر في {days_seen} يوم** · "
            f"**أعلى نقاط:** {item.max_score:.0f} · **تطابق:** {item.taste:.0%}"
        )
        if item.meta.get("repo"):
            out.append(
                f"- **المستودع:** {item.meta['repo']} · ⭐ {item.meta.get('stars', 0)}"
            )
        out.append(f"- [افتح الرابط]({item.url})")
        out.append("")

    out += ["## حسب الثيم", ""]
    for topic in TOPIC_ORDER:
        bucket = by_topic.get(topic)
        if not bucket:
            continue
        out.append(f"### {TOPIC_LABEL.get(topic, topic)} ({len(bucket)})")
        out.append("")
        for item in bucket[:7]:
            mark = f" · {len(item.days)}ي" if len(item.days) > 1 else ""
            out.append(f"- [{item.title[:110]}]({item.url}){mark}")
        out.append("")

    # The writers the reader chose to follow are not ranked like news; give
    # them a fixed shelf so a quiet newsletter is still seen.
    letters = [i for i in items if "newsletter" in i.sources][:6]
    if letters:
        out += ["## من النشرات", ""]
        for item in letters:
            outlet = (item.meta or {}).get("outlet") or "نشرة"
            out.append(f"- **{outlet}** — [{item.title[:120]}]({item.url})")
        out.append("")

    people = [i for i in items if "x_account" in i.sources][:6]
    if people:
        out += ["## من الباحثين على X", ""]
        for item in people:
            author = (item.meta or {}).get("author") or ""
            out.append(f"- {author} — [{item.title[:120]}]({item.url})")
        out.append("")

    sources_all: dict[str, int] = {}
    for item in items:
        for s in item.sources:
            sources_all[s] = sources_all.get(s, 0) + 1
    out += ["## توزيع المصادر", "", "| المصدر | قصص |", "|---|---|"]
    for s, c in sorted(sources_all.items(), key=lambda kv: -kv[1]):
        out.append(f"| {SOURCE_LABEL.get(s, s)} | {c} |")
    out.append("")
    return "\n".join(out)


def summarise_period(items: list[Item], limit: int = 20) -> str:
    """Optional: five Arabic bullets over the period, from the top titles."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key or not items:
        return ""
    from .summarize import _API, _MODEL, _post

    titles = "\n".join(f"- {i.title[:180]}" for i in items[:limit])
    prompt = (
        "هاي أهم الأخبار التقنية لآخر فترة. اكتب 5 نقاط عربية مختصرة (سطر لكل نقطة) "
        "توضح التحولات الحقيقية، مو قائمة عناوين. بلا مقدمات.\n\n" + titles
    )
    try:
        data = _post(
            _API,
            {
                "model": _MODEL,
                "temperature": 0.3,
                "max_tokens": 700,
                "messages": [{"role": "user", "content": prompt}],
            },
            key,
        )
        return (data["choices"][0]["message"]["content"] or "").strip()
    except Exception as exc:  # noqa: BLE001
        print(f"[catchup] summary skipped: {exc}")
        return ""


def localize_records(records: list[dict]) -> int:
    """Translate displayed archive records and persist translations back to history."""
    grouped: dict[str, list[dict]] = {}
    for row in records:
        if not isinstance(row, dict) or not row.get("title") or not row.get("url"):
            continue
        identity = str(row.get("id") or row.get("url"))
        grouped.setdefault(identity, []).append(row)
    pending = [
        rows[0]
        for rows in grouped.values()
        if any(not row.get("title_ar") or not row.get("ar") for row in rows)
    ]
    if not pending:
        return 0

    from .models import Signal
    from .rank import Story
    from .summarize import summarize

    stories: list[Story] = []
    records_by_signal_id: dict[str, list[dict]] = {}
    for row in pending:
        sources = {str(source) for source in row.get("sources") or [] if source}
        topics = {str(topic) for topic in row.get("topics") or [] if topic}
        topic = str(row.get("topic") or next(iter(topics), "general"))
        signal = Signal(
            title=str(row.get("title") or ""),
            url=str(row.get("url") or ""),
            source=sorted(sources)[0] if sources else "news",
            topic=topic,
            summary=str(row.get("ar") or ""),
        )
        stories.append(
            Story(
                lead=signal,
                sources=sources,
                topics=topics,
                score=float(row.get("score") or 0),
                taste=float(row.get("taste") or 0),
            )
        )
        identity = str(row.get("id") or row.get("url"))
        records_by_signal_id[signal.id] = grouped[identity]

    translations: dict[str, dict[str, str]] = {}
    localized_count = 0
    for offset in range(0, len(stories), 15):
        batch = stories[offset : offset + 15]
        result = summarize(batch, limit=len(batch))
        for signal_id, fields in result.items():
            rows = records_by_signal_id.get(signal_id)
            if not rows:
                continue
            changed: dict[str, str] = {}
            row_changed = False
            for row in rows:
                for name in ("title_ar", "ar"):
                    value = str(fields.get(name) or "").strip()
                    if value and not row.get(name):
                        row[name] = value
                        changed[name] = value
                        row_changed = True
            if row_changed:
                translations[str(rows[0].get("id") or signal_id)] = changed
                localized_count += 1

    if translations:
        archive.update_localizations(translations)
    return localized_count


def write_report(days: int = 30, top: int = 25, *, use_ai: bool = True,
                 out_path: str | None = None) -> Path:
    items = load_items(days)
    headline = summarise_period(items) if use_ai else ""

    # The static site renders this brief directly. Translate its visible records
    # once, then backfill the archive so later runs do not spend tokens again.
    brief = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stories": [item.to_dict() for item in items[:top]],
        "shelves": {
            "newsletters": [
                item.to_dict() for item in items if "newsletter" in item.sources
            ][:6],
            "researchers": [
                item.to_dict() for item in items if "x_account" in item.sources
            ][:8],
        },
    }
    if use_ai:
        records = brief["stories"] + brief["shelves"]["newsletters"] + brief["shelves"]["researchers"]
        localize_records(records)
        by_id = {str(row.get("id") or row.get("url")): row for row in records}
        by_url = {str(row.get("url")): row for row in records if row.get("url")}
        for item in items:
            row = by_id.get(item.story_id) or by_url.get(item.url)
            if row:
                item.title_ar = item.title_ar or str(row.get("title_ar") or "")
                item.ar = item.ar or str(row.get("ar") or "")

    text = render_report(days, top, headline)
    path = Path(out_path or f"{config.DIGEST_DIR}/catchup-{datetime.now(timezone.utc):%Y-%m-%d}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    Path("data").mkdir(exist_ok=True)
    Path("data/brief.json").write_text(
        json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[catchup] {len(items)} stories -> {path}")
    return path


def write_rolling(days: int = 30, top: int = 30) -> Path:
    """CATCHUP.md at the repo root — always the current picture."""
    items = load_items(days)
    text = render_report(days, top, "")
    path = Path("CATCHUP.md")
    path.write_text(text, encoding="utf-8")
    print(f"[catchup] rolling brief -> {path} ({len(items)} stories)")
    return path
