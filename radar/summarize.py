"""Arabic summaries.

Optional by design: without GROQ_API_KEY the digest still renders, just with
the original titles. With a key, the top stories get one Arabic sentence each
that says what happened and why it matters — not a translation of the title.
"""

from __future__ import annotations

import json
import os
import re

from .http import get_json
from .rank import Story

_API = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

_PROMPT = """أنت محرر تقني عراقي. عندك قائمة إشارات تقنية من آخر يومين.
لكل واحدة اكتب سطراً عربياً واحداً (١٥-٣٠ كلمة) يوضح:
1) شنو صار بالضبط، 2) ليش يهم القارئ التقني.
بلا مبالغة، بلا حشو، بلا ترجمة حرفية للعنوان. استخدم المصطلح الإنكليزي إذا هو الأشهر.
أرجع JSON فقط بالشكل: {{"items":[{{"id":"<id>","ar":"<السطر>"}}]}}

الإشارات:
{items}"""


def _key() -> str:
    return os.getenv("GROQ_API_KEY", "").strip()


def _post(url: str, payload: dict, key: str) -> dict:
    import urllib.error
    import urllib.request

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "tech-radar/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def summarize(stories: list[Story], limit: int = 10) -> dict[str, str]:
    key = _key()
    if not key:
        return {}

    items = [
        {"id": s.lead.id, "title": s.lead.title[:300], "source": s.lead.source}
        for s in stories[:limit]
    ]
    if not items:
        return {}

    payload = {
        "model": _MODEL,
        "temperature": 0.2,
        "max_tokens": 1400,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": _PROMPT.format(
                    items=json.dumps(items, ensure_ascii=False)
                ),
            }
        ],
    }

    try:
        data = _post(_API, payload, key)
        text = data["choices"][0]["message"]["content"] or ""
    except Exception as exc:  # noqa: BLE001 - summarising is best-effort
        print(f"[summarize] skipped: {exc}")
        return {}

    text = re.sub(r"```json|```", "", text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            print(f"[summarize] non-JSON response: {text[:160]!r}")
            return {}
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            print(f"[summarize] non-JSON response: {text[:160]!r}")
            return {}

    out: dict[str, str] = {}
    for item in parsed.get("items", []):
        sid, ar = item.get("id"), (item.get("ar") or "").strip()
        if sid and ar:
            out[sid] = ar
    return out
