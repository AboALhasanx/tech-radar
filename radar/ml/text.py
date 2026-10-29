"""Text normalisation and tokenisation for the taste model.

Arabic needs its own pass: alef/ya/ta-marbuta variants and diacritics make the
same word look like three different features otherwise.
"""

from __future__ import annotations

import re

URL_RE = re.compile(r"https?://\S+")
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#(\w+)")
NUM_RE = re.compile(r"\b\d[\d,.]*\b")
WS_RE = re.compile(r"\s+")
WORD_RE = re.compile(r"[a-z0-9][a-z0-9'\-]*|[\u0600-\u06FF]+")

_AR_DIACRITICS = re.compile(r"[\u064B-\u0652\u0670\u0640]")

STOP_EN = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "is",
    "are", "was", "were", "be", "been", "it", "its", "this", "that", "these",
    "those", "as", "at", "by", "from", "has", "have", "had", "will", "would",
    "can", "could", "should", "not", "no", "but", "if", "then", "than", "so",
    "we", "you", "they", "he", "she", "i", "my", "our", "your", "their", "them",
    "us", "me", "do", "does", "did", "just", "now", "new", "get", "got", "make",
    "made", "like", "more", "most", "very", "out", "up", "about", "into", "over",
    "after", "before", "here", "there", "what", "when", "how", "why", "who",
}

STOP_AR = {
    "من", "في", "على", "إلى", "الى", "عن", "هذا", "هذه", "ذلك", "التي", "الذي",
    "مع", "كان", "كانت", "ما", "لا", "أن", "ان", "إن", "و", "أو", "او", "ثم",
    "قد", "كل", "بعد", "قبل", "هو", "هي", "هم", "نحن", "لكن", "حتى", "بين",
    "عند", "يكون", "تم", "كما", "هناك", "أي", "اي",
}


def normalize(text: str) -> str:
    text = (text or "").lower()
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = HASHTAG_RE.sub(r" \1 ", text)
    text = NUM_RE.sub(" <num> ", text)
    text = _AR_DIACRITICS.sub("", text)
    text = (
        text.replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ى", "ي")
        .replace("ة", "ه")
        .replace("ؤ", "و")
        .replace("ئ", "ي")
    )
    return WS_RE.sub(" ", text).strip()


def tokens(text: str) -> list[str]:
    out: list[str] = []
    for word in WORD_RE.findall(normalize(text)):
        if word == "<num>":
            continue
        if word in STOP_EN or word in STOP_AR:
            continue
        if len(word) < 2:
            continue
        out.append(word)
    return out


def ngrams(text: str) -> list[str]:
    """Unigrams plus adjacent bigrams, marked so they cannot collide."""
    words = tokens(text)
    grams = list(words)
    grams += [f"{a}_{b}" for a, b in zip(words, words[1:])]
    return grams


def shape_features(text: str) -> dict[str, float]:
    """Cheap structural signals that carry taste information on their own."""
    raw = text or ""
    return {
        "len_log": len(raw) ** 0.5,
        "has_code": 1.0 if ("`" in raw or "```" in raw) else 0.0,
        "has_version": 1.0 if re.search(r"\b[vo]?\d+\.\d+", raw) else 0.0,
        "has_percent": 1.0 if "%" in raw else 0.0,
        "has_benchmark": 1.0 if re.search(r"(bench|sota|eval|score|accuracy|latency|tok/s)", raw, re.I) else 0.0,
        "has_arabic": 1.0 if re.search(r"[\u0600-\u06FF]", raw) else 0.0,
        "n_links": len(URL_RE.findall(raw)),
        "n_lines": raw.count("\n"),
    }
