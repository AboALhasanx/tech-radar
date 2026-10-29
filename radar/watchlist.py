"""Keyword watchlist: the few things worth interrupting a busy person for."""

from __future__ import annotations

import json
from pathlib import Path

from .rank import Story

DEFAULT_PATH = "radar/watchlist.json"

# Tuned for this profile: agents/System-1, OCR, mobile, Arabic/RTL, testing.
DEFAULT = {
    "min_score": 50,
    "keywords": [
        "jev", "system 1", "system one", "non-autoregressive", "diffusion llm",
        "ocr", "document parsing", "minicpm", "jina-ocr",
        "expo", "react native", "flutter", "android studio", "kotlin multiplatform",
        "playwright", "maestro", "e2e", "fuzzing", "test",
        "rtl", "arabic", "عربي", "bidi",
        "mcp", "harness", "agent", "skill",
        "deepseek", "qwen", "kimi", "glm",
    ],
}


def load(path: str = DEFAULT_PATH) -> dict:
    p = Path(path)
    if not p.exists():
        return dict(DEFAULT)
    try:
        data = json.loads(p.read_text("utf-8"))
    except json.JSONDecodeError:
        return dict(DEFAULT)
    return {
        "min_score": float(data.get("min_score", DEFAULT["min_score"])),
        "keywords": [k.lower() for k in data.get("keywords", DEFAULT["keywords"])],
    }


def match(story: Story, keywords: list[str]) -> list[str]:
    text = " ".join(
        [story.lead.title, story.lead.summary or ""]
        + [m.title for m in story.members]
    ).lower()
    return [k for k in keywords if k in text]


def check(stories: list[Story], cfg: dict | None = None) -> list[tuple[Story, list[str]]]:
    cfg = cfg or load()
    floor = cfg["min_score"]
    out: list[tuple[Story, list[str]]] = []
    for story in stories:
        if story.score < floor:
            continue
        hits = match(story, cfg["keywords"])
        if hits:
            out.append((story, hits))
    return out
