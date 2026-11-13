"""Arabic titles and explanations for the top stories."""

from __future__ import annotations

import json
import os
import re

from .http import get_json
from .rank import Story

_API = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

_PROMPT = """أنت محرر تقني عربي. حوّل كل خبر إلى عنوان عربي واضح وشرح موجز.
لكل خبر:
1) title_ar: ترجمة أمينة للعنوان، مع إبقاء أسماء المنتجات والمصطلحات المعروفة بالإنكليزية عند الحاجة.
2) ar: جملة أو جملتان بالعربية السهلة تشرحان ما الذي حدث ولماذا يهم، اعتماداً فقط على العنوان والمقتطف.
لا تخترع تفاصيل أو أرقاماً. إذا لم يكفِ النص، وضّح أن التفاصيل محدودة.
أرجع JSON فقط بالشكل: {{"items":[{{"id":"<id>","title_ar":"<العنوان بالعربية>","ar":"<الشرح>"}}]}}

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


def summarize(stories: list[Story], limit: int = 15) -> dict[str, dict[str, str]]:
    key = _key()
    if not key:
        return {}

    items = [
        {
            "id": s.lead.id,
            "title": s.lead.title[:300],
            "context": (s.lead.summary or "")[:500],
            "source": s.lead.source,
        }
        for s in stories[:limit]
    ]
    if not items:
        return {}

    payload = {
        "model": _MODEL,
        "temperature": 0.2,
        # Leave room for the period summary under the current 1,000-token free quota.
        "max_tokens": 700,
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

    out: dict[str, dict[str, str]] = {}
    for item in parsed.get("items", []):
        if not isinstance(item, dict):
            continue
        sid = item.get("id")
        title_ar = (item.get("title_ar") or "").strip()
        ar = (item.get("ar") or "").strip()
        if sid and (title_ar or ar):
            out[str(sid)] = {"title_ar": title_ar, "ar": ar}
    return out
