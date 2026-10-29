"""Markdown + JSON rendering."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .rank import Story

SOURCE_LABEL = {
    "x": "X",
    "news": "صحافة",
    "hackernews": "Hacker News",
    "reddit": "Reddit",
    "github": "GitHub",
    "mastodon": "Mastodon",
    "paper": "ورقة بحثية",
}

TOPIC_LABEL = {
    "ai": "ذكاء اصطناعي",
    "agents": "وكلاء",
    "opensource": "مفتوح المصدر",
    "devtools": "أدوات مطوّرين",
    "arabic": "عربي / RTL",
    "mobile": "موبايل",
    "dev": "تطوير",
    "hardware": "عتاد",
    "community": "مجتمع",
    "code": "كود",
    "general": "عام",
    "research": "بحث علمي",
    "writing": "كتابة علمية",
    "reasoning": "استدلال",
    "learning": "تعلّم وتحسين أكاديمي",
}


def _fmt_date(dt: datetime | None) -> str:
    if not dt:
        return "—"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _story_block(idx: int, story: Story, summary: str | None) -> str:
    sources = ", ".join(SOURCE_LABEL.get(s, s) for s in sorted(story.sources))
    lines = [f"### {idx}. {story.lead.title}", ""]
    if summary:
        lines += [summary, ""]
    lines.append(f"- **المصادر:** {sources}")
    lines.append(f"- **النقاط:** {story.score:.1f} · **التفاعل:** {int(story.total_engagement)}")
    if story.taste:
        lines.append(f"- **تطابق مع ذوقك:** {story.taste:.0%}")
    if story.niche_hits:
        lines.append(f"- **صلة بتخصصك:** {', '.join(story.niche_hits)}")
    if story.lead.meta.get("repo"):
        m = story.lead.meta
        lines.append(f"- **المستودع:** {m['repo']} · ⭐ {m.get('stars', 0)} · {m.get('language') or '—'}")
    lines.append(f"- [افتح الرابط]({story.lead.url})")
    lines.append("")
    return "\n".join(lines)


def render_markdown(
    stories: list[Story],
    *,
    summaries: dict[str, str] | None = None,
    fetched: int = 0,
) -> str:
    summaries = summaries or {}
    now = datetime.now(timezone.utc)
    source_counts: dict[str, int] = {}
    for story in stories:
        for member in story.members:
            source_counts[member.source] = source_counts.get(member.source, 0) + 1

    out = [
        f"# رادار التقنيات — {now:%Y-%m-%d}",
        "",
        f"> {fetched} إشارة من {len(source_counts)} مصادر · {len(stories)} قصة بعد التجميع",
        "",
    ]

    # Research first: this radar exists to keep an academic current, so the
    # papers and writing tools lead the digest.
    research = [
        s for s in stories if s.topics & config.RESEARCH_TOPICS or "paper" in s.sources
    ]
    if research:
        out += ["## البحث والكتابة العلمية", ""]
        for i, story in enumerate(research[:8], 1):
            out.append(_story_block(i, story, summaries.get(story.lead.id)))

    x_stories = [s for s in stories if "x" in s.sources and s not in research]
    if x_stories:
        out += ["## ما يدور على X", ""]
        for i, story in enumerate(x_stories[:6], 1):
            out.append(_story_block(i, story, summaries.get(story.lead.id)))

    rest = [s for s in stories if s not in research and s not in x_stories]
    if rest:
        out += ["## أخبار ومصادر ثانية", ""]
        for i, story in enumerate(rest, 1):
            out.append(_story_block(i, story, summaries.get(story.lead.id)))

    out += ["## إحصاءات المصادر", "", "| المصدر | عدد الإشارات |", "|---|---|"]
    for source, count in sorted(source_counts.items(), key=lambda kv: -kv[1]):
        out.append(f"| {SOURCE_LABEL.get(source, source)} | {count} |")
    out.append("")
    out.append(f"<sub>تم التوليد آلياً · {now:%Y-%m-%d %H:%M} UTC</sub>")
    return "\n".join(out)


def write_outputs(
    stories: list[Story],
    *,
    summaries: dict[str, str] | None = None,
    fetched: int = 0,
    digest_dir: str = "digest",
    data_dir: str = "data",
) -> tuple[Path, Path]:
    now = datetime.now(timezone.utc)
    Path(digest_dir).mkdir(parents=True, exist_ok=True)
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    md_path = Path(digest_dir) / f"{now:%Y-%m-%d}.md"
    md_path.write_text(
        render_markdown(stories, summaries=summaries, fetched=fetched),
        encoding="utf-8",
    )

    json_path = Path(data_dir) / "latest.json"
    payload = {
        "generated_at": now.isoformat(),
        "fetched": fetched,
        "stories": [
            {**s.lead.to_dict(), "sources": sorted(s.sources), "score": s.score,
             "taste": s.taste, "ar": (summaries or {}).get(s.lead.id, "")}
            for s in stories
        ],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, json_path
