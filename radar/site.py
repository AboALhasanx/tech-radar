"""Static site + RSS built from data/latest.json.

GitHub Pages serves this for free, and the feed lets any reader app subscribe.
No server, no bot process, no hosting bill.
"""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit

from . import site_pwa
from .render import SOURCE_LABEL, TOPIC_LABEL

SITE_DIR = "site"
SITE_URL = "https://aboalhasanx.github.io/tech-radar/"

RESEARCH = {"research_tools", "harness", "free", "launch"}

def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _merge_localizations(data: dict, latest: dict) -> dict:
    newest = {}
    for story in latest.get("stories") or []:
        if not isinstance(story, dict):
            continue
        if story.get("id"):
            newest[story["id"]] = story
        if story.get("url"):
            newest[story["url"]] = story
    for story in data.get("stories") or []:
        if not isinstance(story, dict):
            continue
        extra = newest.get(story.get("id") or story.get("url")) or newest.get(story.get("url")) or {}
        for field in ("title_ar", "ar"):
            if not story.get(field) and extra.get(field):
                story[field] = extra[field]
    return data


def _load() -> dict:
    brief = _read_json(Path("data/brief.json"))
    latest = _read_json(Path("data/latest.json"))
    data = latest if latest.get("stories") else brief
    if not isinstance(data.get("stories"), list):
        data["stories"] = []

    # Keep curated shelves when the latest collection file has no shelf data.
    shelves = data.get("shelves") or {}
    for source in (brief, latest):
        if source is data:
            continue
        for name, items in (source.get("shelves") or {}).items():
            if not shelves.get(name) and items:
                shelves[name] = items
    if shelves:
        data["shelves"] = shelves

    return _merge_localizations(data, latest)


def _is_research(story: dict) -> bool:
    return bool(RESEARCH & set(story.get("topics") or [])) or "paper" in (
        story.get("sources") or []
    )


def _plain(value: str | None) -> str:
    return " ".join(str(value or "").split())


def _safe_url(value: str | None) -> str:
    value = str(value or "").strip()
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else ""


def _slug(story: dict) -> str:
    candidate = re.sub(r"[^A-Za-z0-9_-]+", "-", str(story.get("id") or "")).strip("-")
    if not candidate:
        source = str(story.get("url") or "") + "|" + str(story.get("title") or "")
        candidate = sha256(source.encode("utf-8")).hexdigest()[:20]
    return candidate[:64]


def _labels(story: dict) -> list[str]:
    sources = [SOURCE_LABEL.get(source, source) for source in story.get("sources") or []]
    topics = story.get("topics") or [story.get("topic") or "general"]
    return sources + [TOPIC_LABEL.get(topic, topic) for topic in topics[:2]]


def _save_button(page: str, file: str) -> str:
    return (
        f'<button class="save-button" type="button" data-save-page="{html.escape(page, quote=True)}" '
        f'data-save-file="{html.escape(file, quote=True)}" aria-pressed="false">حفظ دون إنترنت</button>'
        '<span class="save-status" data-save-status role="status" aria-live="polite"></span>'
    )


def _card(story: dict, *, feature: bool = False) -> str:
    slug = _slug(story)
    title = _plain(story.get("title_ar") or story.get("title"))
    original = _plain(story.get("title"))
    summary = _plain(story.get("ar"))
    detail = f"./stories/{slug}.html"
    download = f"./downloads/{slug}.md"
    labels = "".join(
        f'<span class="tag">{html.escape(label)}</span>' for label in _labels(story)
    )
    try:
        score = f"{float(story.get('score') or 0):.0f}"
    except (TypeError, ValueError):
        score = "0"
    original_html = (
        f'<p class="original-title" dir="auto">{html.escape(original)}</p>'
        if original and title != original else ""
    )
    summary_html = f'<p class="story-summary">{html.escape(summary)}</p>' if summary else ""
    class_name = "story story--feature" if feature else "story"
    return (
        f'<li class="{class_name}"><a class="story-title" href="{detail}">{html.escape(title)}</a>'
        f"{original_html}{summary_html}"
        f'<div class="story-meta">{labels}<span class="score">{score}</span></div>'
        f'<div class="story-actions">{_save_button(detail, download)}</div></li>'
    )


def _section(title: str, stories: list[dict]) -> str:
    if not stories:
        return ""
    cards = "".join(
        _card(story, feature=index == 0) for index, story in enumerate(stories)
    )
    return (
        f'<section class="section"><div class="section-heading"><h2>{html.escape(title)}</h2>'
        f'<span>{len(stories)} قصة</span></div><ol class="story-list">{cards}</ol></section>'
    )


def _site_header(root: str = "./") -> str:
    return (
        '<header class="site-header">'
        f'<a class="brand" href="{root}"><img src="{root}icons/icon.svg" alt="" width="42" height="42">'
        '<span>رادار التقنيات<small>TECH RADAR</small></span></a>'
        '<nav class="nav" aria-label="التنقل">'
        f'<a href="{root}saved.html">المحفوظات</a>'
        f'<a href="{root}feed.xml">RSS</a>'
        '<button type="button" data-install hidden>تثبيت التطبيق</button>'
        '<span class="network-state" data-network-state role="status" aria-live="polite"></span>'
        '</nav></header>'
    )


def _page(title: str, body: str, *, root: str = "./", extra_head: str = "") -> str:
    return f"""<!doctype html>
<html lang="ar" dir="rtl" data-root="{root}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0e1115">
<meta name="description" content="موجز تقني عربي مع حفظ الملخصات للقراءة دون إنترنت">
<link rel="manifest" href="{root}manifest.webmanifest">
<link rel="icon" href="{root}icons/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{root}icons/icon-192.png">
<link rel="stylesheet" href="{root}app.css">
<script defer src="{root}app.js"></script>
{extra_head}
<title>{html.escape(title)}</title>
</head>
<body>
<div class="wrap">
{_site_header(root)}
<main>{body}</main>
<footer class="site-footer">الموجز وملخص الخبر ينحفظان على جهازك عند اختيار الحفظ. رابط الخبر الأصلي يحتاج اتصالاً.
<a href="https://github.com/AboALhasanx/tech-radar" target="_blank" rel="noopener noreferrer">المشروع على GitHub</a></footer>
</div>
</body>
</html>
"""


def _story_markdown(story: dict) -> str:
    title = _plain(story.get("title_ar") or story.get("title"))
    original = _plain(story.get("title"))
    summary = _plain(story.get("ar")) or "لا يتوفر ملخص عربي لهذا الخبر حالياً."
    url = _safe_url(story.get("url"))
    rows = [f"# {title}", ""]
    if original and original != title:
        rows += [f"**العنوان الأصلي:** {original}", ""]
    rows += [summary, ""]
    if url:
        rows += [f"[افتح الخبر الأصلي]({url})", ""]
    rows += ["— تم حفظه من رادار التقنيات."]
    return "\n".join(rows) + "\n"


def _detail_page(story: dict, slug: str) -> str:
    root = "../"
    title = _plain(story.get("title_ar") or story.get("title")) or "خبر تقني"
    original = _plain(story.get("title"))
    summary = _plain(story.get("ar"))
    url = _safe_url(story.get("url"))
    labels = "".join(
        f'<span class="tag">{html.escape(label)}</span>' for label in _labels(story)
    )
    original_html = (
        f'<p class="detail-original" dir="auto">{html.escape(original)}</p>'
        if original and original != title else ""
    )
    summary_text = summary or (
        "لم يصل شرح عربي لهذا الخبر بعد. يمكنك فتح الرابط الأصلي أو العودة لاحقاً بعد تحديث الموجز."
    )
    source_link = (
        f'<a class="primary-link" href="{html.escape(url, quote=True)}" target="_blank" '
        'rel="noopener noreferrer">افتح الخبر الأصلي</a>'
        if url else '<span class="detail-note">رابط المصدر غير متوفر.</span>'
    )
    file_path = f"../downloads/{slug}.md"
    extra_head = (
        f'<meta name="story-title" content="{html.escape(title, quote=True)}">'
        f'<meta name="story-summary" content="{html.escape(summary, quote=True)}">'
        f'<meta name="offline-file" content="{file_path}">'
    )
    body = (
        '<article class="detail">'
        f'<h1>{html.escape(title)}</h1>{original_html}'
        f'<div class="detail-meta">{labels}</div>'
        '<section class="summary-panel"><h2>شنو صار؟</h2>'
        f'<p>{html.escape(summary_text)}</p></section>'
        f'<div class="story-actions">{source_link}</div>'
        '<p class="detail-note">يحفظ التطبيق هذه الصفحة وملف الملخص فقط. صفحة الناشر أو PDF خارجي يحتاج الإنترنت.</p>'
        f'<div class="story-actions">{_save_button("../stories/" + slug + ".html", file_path)}'
        f'<a class="secondary-link" href="{file_path}" download>تنزيل الملخص Markdown</a></div></article>'
    )
    return _page(title, body, root=root, extra_head=extra_head)


def _saved_page() -> str:
    body = (
        '<section class="page-heading"><p class="kicker">على هذا الجهاز</p>'
        '<h1>المحفوظات</h1><p class="lede">القصص التي حفظتها وملفات Markdown المتاحة دون اتصال.</p>'
        '<button class="quiet-button" type="button" data-clear-saved>مسح كل المحفوظات</button></section>'
        '<ol class="saved-list" data-saved-list aria-live="polite"></ol>'
    )
    return _page("المحفوظات دون إنترنت", body)


def _offline_page() -> str:
    body = (
        '<section class="page-heading"><p class="kicker">وضع أوفلاين</p>'
        '<h1>هذا الرابط غير محفوظ بعد</h1>'
        '<p class="lede">اتصل بالإنترنت مرة واحدة لحفظ هذا الملخص، أو افتح القصص التي حفظتها مسبقاً.</p>'
        '<div class="story-actions"><a class="primary-link" href="./saved.html">افتح المحفوظات</a>'
        '<a class="secondary-link" href="./index.html">العودة للموجز</a></div></section>'
    )
    return _page("لا يوجد اتصال", body)


def build(out_dir: str = SITE_DIR) -> Path:
    data = _load()
    stories = [s for s in data.get("stories") or [] if isinstance(s, dict)]
    shelves = data.get("shelves") or {}
    all_stories = list(stories)
    known_urls = {s.get("url") for s in stories if s.get("url")}
    for shelf in ("researchers", "newsletters"):
        for story in shelves.get(shelf) or []:
            if isinstance(story, dict) and story.get("url") not in known_urls:
                all_stories.append(story)
                known_urls.add(story.get("url"))

    generated = str(data.get("generated_at") or datetime.now(timezone.utc).isoformat())
    try:
        generated_dt = datetime.fromisoformat(generated.replace("Z", "+00:00"))
        generated_text = generated_dt.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        generated_text = generated
    version = re.sub(r"[^0-9A-Za-z_-]", "", generated)[:24] or "1"

    research = [s for s in stories if _is_research(s)]
    x_items = [s for s in stories if "x" in (s.get("sources") or []) and s not in research]
    rest = [s for s in stories if s not in research and s not in x_items]
    body = (
        '<section class="page-heading">'
        '<h1>أخبار التقنية</h1>'
        f'<p class="lede">{len(stories)} قصة منتقاة، عناوينها مترجمة وملخصاتها بالعربية حيث تتوفر.</p>'
        f'<p class="update-line">آخر تحديث: {html.escape(generated_text)}</p></section>'
        + _section("أدوات، هارنس، ومجاني", research)
        + _section("ما يدور على X", x_items)
        + _section("أخبار ومصادر ثانية", rest)
    )
    for key, title in (("researchers", "من الباحثين على X"), ("newsletters", "من النشرات")):
        rows = [s for s in shelves.get(key) or [] if isinstance(s, dict)]
        body += _section(title, rows)

    index = _page("رادار التقنيات — موجز عربي", body)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "stories").mkdir(parents=True, exist_ok=True)
    (out / "downloads").mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(index, encoding="utf-8")
    (out / "saved.html").write_text(_saved_page(), encoding="utf-8")
    (out / "offline.html").write_text(_offline_page(), encoding="utf-8")
    (out / "feed.xml").write_text(_feed(stories, generated), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")

    for story in all_stories:
        slug = _slug(story)
        (out / "stories" / f"{slug}.html").write_text(
            _detail_page(story, slug), encoding="utf-8"
        )
        (out / "downloads" / f"{slug}.md").write_text(
            _story_markdown(story), encoding="utf-8"
        )

    site_pwa.write_assets(out, version)
    print(f"[site] {len(stories)} stories -> {out}/index.html")
    return out


def _feed(stories: list[dict], generated: str) -> str:
    items = []
    try:
        build_date = datetime.fromisoformat(generated.replace("Z", "+00:00"))
        if build_date.tzinfo is None:
            build_date = build_date.replace(tzinfo=timezone.utc)
        last_build_date = format_datetime(build_date)
    except ValueError:
        last_build_date = ""
    for story in stories[:40]:
        original = _plain(story.get("title"))
        localized = _plain(story.get("title_ar") or original)
        title = html.escape(localized)
        url = html.escape(_safe_url(story.get("url")), quote=True)
        desc = html.escape(_plain(story.get("ar")))
        if original and original != localized:
            desc = f"{html.escape(original)} — {desc}"
        sources = ", ".join(SOURCE_LABEL.get(s, s) for s in story.get("sources") or [])
        items.append(
            f"<item><title>{title}</title><link>{url}</link>"
            f"<guid isPermaLink='false'>{html.escape(str(story.get('id') or url))}</guid>"
            f"<description>{desc} ({html.escape(sources)})</description></item>"
        )
    return (
        "<?xml version='1.0' encoding='utf-8'?>"
        "<rss version='2.0'><channel>"
        "<title>رادار التقنيات</title>"
        f"<link>{SITE_URL}</link>"
        "<description>أهم ما يجري في التقنيات، والأبحاث، والكتابة العلمية</description>"
        + (f"<lastBuildDate>{html.escape(last_build_date)}</lastBuildDate>" if last_build_date else "")
        + "".join(items)
        + "</channel></rss>"
    )


if __name__ == "__main__":
    build()
