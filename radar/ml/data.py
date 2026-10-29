"""Dataset assembly for the taste model.

Positives are posts the account actually liked.
Negatives are the two things it must learn to say no to:
  * hard negatives — posts from accounts it follows that it did *not* like
  * easy negatives — unrelated feed noise (sports, celebrity, politics)
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Example:
    text: str
    label: int
    source: str
    url: str = ""
    when: str = ""


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text("utf-8"))


def _clean(text: str) -> str:
    return (text or "").replace("\n", " ").strip()


def build(
    *,
    likes_path: str = "data/x_likes.json",
    history_path: str = "data/x_history_60d.json",
    negatives_path: str = "data/x_negatives.json",
    min_chars: int = 40,
    seed: int = 13,
) -> list[Example]:
    likes = _load(Path(likes_path))
    history = _load(Path(history_path))
    noise = _load(Path(negatives_path))

    liked_urls = {p.get("url") for p in likes if p.get("url")}

    examples: list[Example] = []
    for post in likes:
        text = _clean(post.get("text"))
        if len(text) >= min_chars:
            examples.append(Example(text, 1, "like", post.get("url", ""), post.get("when", "")))

    for post in history:
        if post.get("url") in liked_urls:
            continue
        text = _clean(post.get("text"))
        if len(text) >= min_chars:
            examples.append(Example(text, 0, "followed", post.get("url", ""), post.get("when", "")))

    for post in noise:
        text = _clean(post.get("text"))
        if len(text) >= min_chars:
            examples.append(Example(text, 0, "noise", post.get("url", ""), post.get("when", "")))

    random.Random(seed).shuffle(examples)
    return examples


def stats(examples: list[Example]) -> dict:
    pos = sum(e.label for e in examples)
    by_source: dict[str, int] = {}
    for e in examples:
        by_source[e.source] = by_source.get(e.source, 0) + 1
    return {"total": len(examples), "positive": pos, "negative": len(examples) - pos, "by_source": by_source}
