"""Static site + RSS built from data/latest.json.

GitHub Pages serves this for free, and the feed lets any reader app subscribe.
No server, no bot process, no hosting bill.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from .render import SOURCE_LABEL, TOPIC_LABEL

SITE_DIR = "site"
SITE_URL = "https://aboalhasanx.github.io/tech-radar/"

RESEARCH = {"research_tools", "harness", "free", "launch"}

CSS = """
:root{--bg:#0f1115;--card:#171a21;--fg:#e8eaf0;--muted:#9aa3b2;--accent:#f0b46a;--line:#252a34}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:"Noto Naskh Arabic","Segoe UI",Tahoma,sans-serif;line-height:1.8}
.wrap{max-width:820px;margin:0 auto;padding:32px 20px 64px}
header{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:26px}
h1{font-size:26px;margin:0}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.meta{color:var(--muted);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:12px 0}
.card h2{font-size:18px;margin:0 0 6px}
.tag{display:inline-block;font-size:12px;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:1px 9px;margin-inline-end:6px}
.score{color:var(--accent);font-weight:700}
section{margin-top:34px}
h3.sec{font-size:15px;color:var(--muted);letter-spacing:.04em;margin:0 0 10px}
footer{margin-top:48px;border-top:1px solid var(--line);padding-top:16px;color:var(--muted);font-size:13px}
"""


def _load() -> dict:
    # the brief covers the whole window; latest.json is only the last run
    brief = Path("data/brief.json")
    if brief.exists():
        try:
            data = json.loads(brief.read_text("utf-8"))
            if data.get("stories"):
                return data
        except json.JSONDecodeError:
            pass
    path = Path("data/latest.json")
    if not path.exists():
        return {"stories": [], "generated_at": ""}
    return json.loads(path.read_text("utf-8"))


def _is_research(story: dict) -> bool:
    return bool(RESEARCH & set(story.get("topics") or [])) or "paper" in (
        story.get("sources") or []
    )


def _card(story: dict) -> str:
    title = html.escape(story.get("title") or "")
    url = html.escape(story.get("url") or "#")
    sources = "".join(
        f'<span class="tag">{html.escape(SOURCE_LABEL.get(s, s))}</span>'
        for s in story.get("sources") or []
    )
    topic = (story.get("topics") or [story.get("topic") or "general"])[0]
    taste = story.get("taste") or 0
    ar = story.get("ar") or ""
    ar_html = f"<p>{html.escape(ar)}</p>" if ar else ""
    return (
        f'<div class="card"><h2><a href="{url}" target="_blank" rel="noopener">{title}</a></h2>'
        f"{ar_html}"
        f'<div class="meta">{sources}<span class="tag">{html.escape(TOPIC_LABEL.get(topic, topic))}</span>'
        f'<span class="score">{story.get("score", 0):.0f}</span> · تطابق {taste:.0%}</div></div>'
    )


def build(out_dir: str = SITE_DIR) -> Path:
    data = _load()
    stories = data.get("stories") or []
    research = [s for s in stories if _is_research(s)]
    x_items = [s for s in stories if "x" in (s.get("sources") or []) and s not in research]
    rest = [s for s in stories if s not in research and s not in x_items]

    gen = data.get("generated_at") or datetime.now(timezone.utc).isoformat()
    try:
        gen_dt = datetime.fromisoformat(gen.replace("Z", "+00:00"))
        gen_txt = gen_dt.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        gen_txt = gen

    parts = [
        "<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>رادار التقنيات</title>",
        f"<link rel='alternate' type='application/rss+xml' href='feed.xml'>",
        f"<style>{CSS}</style></head><body><div class='wrap'>",
        "<header><h1>رادار التقنيات</h1>",
        f"<div class='meta'>آخر تحديث: {gen_txt} · <a href='feed.xml'>RSS</a> · "
        f"<a href='https://github.com/AboALhasanx/tech-radar/blob/master/CATCHUP.md'>ملخص 30 يوم</a></div></header>",
    ]

    if research:
        parts.append("<section><h3 class='sec'>أدوات، هارنس، ومجاني</h3>")
        parts += [_card(s) for s in research]
        parts.append("</section>")
    if x_items:
        parts.append("<section><h3 class='sec'>ما يدور على X</h3>")
        parts += [_card(s) for s in x_items]
        parts.append("</section>")
    if rest:
        parts.append("<section><h3 class='sec'>أخبار ومصادر ثانية</h3>")
        parts += [_card(s) for s in rest]
        parts.append("</section>")

    parts.append(
        "<footer>يعمل على GitHub Actions · بلا سيرفر · "
        "<a href='https://github.com/AboALhasanx/tech-radar'>الكود</a></footer>"
        "</div></body></html>"
    )

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text("\n".join(parts), encoding="utf-8")
    (out / "feed.xml").write_text(_feed(stories, gen), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    print(f"[site] {len(stories)} stories -> {out}/index.html")
    return out


def _feed(stories: list[dict], generated: str) -> str:
    items = []
    for story in stories[:40]:
        title = html.escape(story.get("title") or "")
        url = html.escape(story.get("url") or "")
        desc = html.escape(story.get("ar") or "")
        sources = ", ".join(SOURCE_LABEL.get(s, s) for s in story.get("sources") or [])
        items.append(
            f"<item><title>{title}</title><link>{url}</link>"
            f"<guid isPermaLink='false'>{html.escape(story.get('id') or url)}</guid>"
            f"<description>{desc} ({html.escape(sources)})</description></item>"
        )
    return (
        "<?xml version='1.0' encoding='utf-8'?>"
        "<rss version='2.0'><channel>"
        "<title>رادار التقنيات</title>"
        f"<link>{SITE_URL}</link>"
        "<description>أهم ما يجري في التقنيات، والأبحاث، والكتابة العلمية</description>"
        f"<lastBuildDate>{html.escape(generated)}</lastBuildDate>"
        + "".join(items)
        + "</channel></rss>"
    )


if __name__ == "__main__":
    build()
