"""Pick a Groq model that can actually return JSON. Diagnostic, not part of the run."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

for line in Path(".env").read_text("utf-8", errors="ignore").splitlines():
    if line.startswith("GROQ_API_KEY="):
        os.environ["GROQ_API_KEY"] = line.split("=", 1)[1].strip()

KEY = os.environ["GROQ_API_KEY"]
URL = "https://api.groq.com/openai/v1/chat/completions"

PROMPT = (
    "أرجع JSON فقط بالشكل {\"items\":[{\"id\":\"1\",\"ar\":\"نص عربي قصير\"}]} "
    "للعنصر التالي: id=1, title=OpenAI releases a new model"
)

for model in ("openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"):
    for use_format in (True, False):
        payload = {
            "model": model,
            "temperature": 0.2,
            "max_tokens": 800,
            "messages": [{"role": "user", "content": PROMPT}],
        }
        if use_format:
            payload["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(
            URL,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {KEY}",
                "Content-Type": "application/json",
                "User-Agent": "tech-radar/1.0",
            },
            method="POST",
        )
        label = f"{model} json_mode={use_format}"
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read())
            text = data["choices"][0]["message"]["content"] or ""
            ok = False
            try:
                json.loads(text.strip())
                ok = True
            except json.JSONDecodeError:
                ok = "{" in text and "}" in text
            print(f"OK   {label}  chars={len(text)}  jsonish={ok}  head={text[:80]!r}")
        except urllib.error.HTTPError as exc:
            print(f"FAIL {label}  {exc.code} {exc.read().decode('utf-8','replace')[:120]}")
        except Exception as exc:
            print(f"ERR  {label}  {exc}")
