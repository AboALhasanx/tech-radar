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
