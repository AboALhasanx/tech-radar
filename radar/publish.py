"""Optional Telegram delivery (same channel pattern as tech_news_bot)."""

from __future__ import annotations

import json
import os

from .rank import Story
from .render import SOURCE_LABEL

_API = "https://api.telegram.org/bot{token}/sendMessage"
_LIMIT = 3800


def enabled() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHANNEL_ID"))


def _send(text: str, token: str, chat_id: str) -> bool:
    import urllib.request

    body = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        _API.format(token=token),
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "tech-radar/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status == 200
    except Exception as exc:  # noqa: BLE001
        print(f"[telegram] {exc}")
        return False


def publish(stories: list[Story], *, top: int = 8) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID", "")
    if not (token and chat_id):
        print("[telegram] no credentials, skipping")
        return False

    lines = ["<b>رادار التقنيات</b>", ""]
    for i, story in enumerate(stories[:top], 1):
        sources = " · ".join(SOURCE_LABEL.get(s, s) for s in sorted(story.sources))
        title = story.lead.title.replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f"<b>{i}.</b> {title}")
        lines.append(f"<i>{sources}</i> — <a href=\"{story.lead.url}\">الرابط</a>")
        lines.append("")

    text = "\n".join(lines)
    if len(text) > _LIMIT:
        text = text[: _LIMIT - 20] + "\n…"

    ok = _send(text, token, chat_id)
    print(f"[telegram] {'sent' if ok else 'failed'}")
    return ok


def publish_alert(items, *, top: int = 4) -> bool:
    """Short, rare, high-signal message for watchlist matches."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID", "")
    if not (token and chat_id) or not items:
        return False

    lines = ["<b>⚡ تنبيه رادار</b>", ""]
    for story, hits in items[:top]:
        title = story.lead.title.replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f"• <a href=\"{story.lead.url}\">{title}</a>")
        lines.append(f"  <i>{' · '.join(hits[:3])}</i>")
    text = "\n".join(lines)[:_LIMIT]
    ok = _send(text, token, chat_id)
    print(f"[telegram] alert {'sent' if ok else 'failed'} ({len(items)} matches)")
    return ok


def publish_catchup(text: str, *, top: int = 6) -> bool:
    """Send the head of a catch-up report (Telegram caps at 4096 chars)."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID", "")
    if not (token and chat_id):
        return False
    body = text[: _LIMIT - 100]
    ok = _send(body, token, chat_id)
    print(f"[telegram] catch-up {'sent' if ok else 'failed'}")
    return ok
