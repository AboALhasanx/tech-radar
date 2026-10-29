"""Mine the scraped X history by theme, so a briefing is built from evidence."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

THEMES = {
    "MOBILE": [
        "flutter", "react native", "expo", "swiftui", "jetpack compose", "kotlin multiplatform",
        "kmp", "android", "ios", "mobile", "impeller", "skia", "hermes",
    ],
    "TESTING": [
        "playwright", "vitest", "testing", "e2e", "end-to-end", "cypress", "maestro",
        "detox", "fuzz", "snapshot test", "screenshot test", "qa", "flake", "coverage",
        "regression", "unit test",
    ],
    "DESIGN": [
        "figma", "design system", "design", "ui", "ux", "typography", "font", "rtl",
        "accessibility", "a11y", "color", "layout", "figma make", "penpot",
    ],
    "OCR_DOCS": [
        "ocr", "document ai", "pdf", "extraction", "parse document", "vlm", "scan",
        "handwriting", "invoice", "layout", "table extraction", "docling", "marker",
        "mistral ocr", "dots.ocr", "paddleocr", "tesseract", "gemini ocr",
    ],
    "SYSTEM1": [
        "system 1", "system1", "non-autoregressive", "diffusion llm", "diffusion model",
        "fast thinking", "chain of thought", "reasoning model", "latent reasoning",
        "dllm", "parallel decoding", "speculative decoding",
    ],
    "CHINA": [
        "deepseek", "qwen", "kimi", "glm", "zhipu", "minimax", "moonshot", "baidu",
        "alibaba", "bytedance", "tencent", "ernie", "stepfun", "01.ai", "yi model",
    ],
    "AGENTS": [
        "agent", "agents", "agentic", "mcp", "claude code", "codex", "harness", "skill",
        "skills", "subagent", "tool use", "tool-use", "context engineering", "opencode",
        "cursor", "copilot",
    ],
    "GITHUB": [
        "github", "repo", "open source", "open-source", "release", "stars", "oss",
    ],
}


def parse_likes(value: str) -> int:
    value = (value or "0").strip().replace(",", "")
    if not value:
        return 0
    mult = 1
    if value[-1] in "Kk":
        mult, value = 1000, value[:-1]
    elif value[-1] in "Mm":
        mult, value = 1_000_000, value[:-1]
    try:
        return int(float(value) * mult)
    except ValueError:
        return 0


def main() -> int:
    posts = json.loads(Path("data/x_history_60d.json").read_text("utf-8"))
    only = {a.upper() for a in sys.argv[1:]}
    themes = {k: v for k, v in THEMES.items() if not only or k in only}
    print(f"corpus: {len(posts)} posts; themes: {', '.join(themes)}\n")

    for theme, keys in themes.items():
        hits = []
        for post in posts:
            text = (post.get("text") or "").lower()
            if any(k in text for k in keys):
                hits.append(post)
        hits.sort(key=lambda p: parse_likes(p.get("likes", "0")), reverse=True)

        print("=" * 100)
        print(f"{theme}  ({len(hits)} posts)")
        print("=" * 100)
        for post in hits[:10]:
            text = (post.get("text") or "").replace("\n", " ").strip()
            if not text:
                continue
            print(
                f"[{parse_likes(post.get('likes','0')):>7}] {post.get('author','')[:40]} "
                f"· {post.get('when','')[:10]}"
            )
            print(f"   {text[:400]}")
            print(f"   {post.get('url','')}")
            print()
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
