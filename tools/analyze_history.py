"""Turn the scraped X history into a readable trend report.

Input : data/x_history_60d.json  (from tools/x_session.py history)
Output: digest/x-history-<n>d.md
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "is",
    "are", "was", "were", "it", "this", "that", "you", "your", "we", "our",
    "they", "from", "at", "by", "as", "has", "have", "will", "can", "not",
    "just", "about", "after", "over", "into", "than", "more", "most", "very",
    "all", "now", "new", "one", "two", "get", "got", "make", "made", "like",
    "what", "when", "how", "why", "who", "its", "it's", "i'm", "i've", "don't",
    "https", "http", "co", "amp", "rt", "www", "com", "also", "would", "could",
    "should", "there", "their", "them", "been", "being", "but", "out", "up",
    "if", "so", "do", "does", "did", "my", "me", "he", "she", "his", "her",
    "من", "في", "على", "إلى", "عن", "هذا", "هذه", "التي", "الذي", "مع", "كان",
    "ما", "لا", "أن", "إن", "و", "أو", "ثم", "قد", "كل", "بعد", "قبل", "هو",
    "هي", "هم", "نحن", "لكن", "حتى", "بين", "عند", "كانت", "يكون",
}

WORD = re.compile(r"[A-Za-z][A-Za-z0-9\-']{2,}|[\u0600-\u06FF]{3,}")

# Themes, not just words: a post counts for a theme if it hits any keyword.
THEMES = {
    "الذكاء الاصطناعي والنماذج": [
        "ai", "llm", "gpt", "claude", "gemini", "model", "openai", "anthropic",
        "deepseek", "qwen", "inference", "training",
    ],
    "الوكلاء (Agents/MCP)": ["agent", "agents", "agentic", "mcp", "tool use", "tool-use"],
    "أدوات المطوّرين": [
        "github", "code", "coding", "ide", "compiler", "typescript", "python",
        "rust", "api", "sdk", "cli",
    ],
    "مفتوح المصدر": ["open source", "open-source", "oss", "mit license", "self-hosted"],
    "عربي / RTL": ["arabic", "rtl", "عربي", "العربية", "bidi", "ترجمة"],
    "موبايل": ["flutter", "react native", "expo", "android", "ios", "mobile"],
    "شركات وتمويل": [
        "funding", "raises", "raised", "valuation", "ipo", "acquisition",
        "acquires", "series a", "series b", "seed",
    ],
    "عتاد وشرائح": ["gpu", "chip", "nvidia", "tpu", "semiconductor", "datacenter"],
    "أمن": ["security", "vulnerability", "cve", "exploit", "breach", "cyber"],
}


def norm(text: str) -> str:
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي").replace("ة", "ه")
    text = re.sub(r"[\u064B-\u0652]", "", text)  # diacritics
    return text.lower()


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


def main(days: int = 60) -> int:
    path = Path(f"data/x_history_{days}d.json")
    if not path.exists():
        print(f"missing {path} — run tools/x_session.py history --days {days}")
        return 1

    posts = json.loads(path.read_text("utf-8"))
    print(f"[analyze] {len(posts)} posts")

    terms: Counter = Counter()
    theme_counts: Counter = Counter()
    by_author: Counter = Counter()
    by_month: dict[str, int] = defaultdict(int)
    author_likes: Counter = Counter()

    for post in posts:
        text = post.get("text") or ""
        low = norm(text)
        for word in WORD.findall(low):
            if word not in STOP:
                terms[word] += 1
        for theme, keys in THEMES.items():
            if any(k in low for k in keys):
                theme_counts[theme] += 1
        author = (post.get("author") or "").split("@")[-1].split()[0] if post.get("author") else "?"
        by_author[author] += 1
        likes = parse_likes(post.get("likes", "0"))
        author_likes[author] += likes
        when = post.get("when") or ""
        if len(when) >= 7:
            by_month[when[:7]] += 1

    top_posts = sorted(posts, key=lambda p: parse_likes(p.get("likes", "0")), reverse=True)[:15]

    out: list[str] = [
        f"# تحليل رجعي — آخر {days} يوم من حسابات تتابعها",
        "",
        f"> {len(posts)} منشور · {len(by_author)} حساب · مصدر: X عبر جلستك المحلية",
        "",
        "## الثيمات الأكثر حضوراً",
        "",
        "| الثيم | عدد المنشورات |",
        "|---|---|",
    ]
    for theme, count in theme_counts.most_common():
        out.append(f"| {theme} | {count} |")

    out += ["", "## أكثر الحسابات نشاطاً", "", "| الحساب | منشورات | إعجابات |", "|---|---|---|"]
    for author, count in by_author.most_common(15):
        out.append(f"| @{author} | {count} | {author_likes[author]:,} |")

    out += ["", "## التوزيع الشهري", "", "| الشهر | منشورات |", "|---|---|"]
    for month, count in sorted(by_month.items()):
        out.append(f"| {month} | {count} |")

    out += ["", "## أعلى المنشورات تفاعلاً", ""]
    for post in top_posts:
        text = (post.get("text") or "").replace("\n", " ").strip()
        out.append(
            f"- **{parse_likes(post.get('likes','0')):,}** — {text[:220]}  \n"
            f"  {post.get('author','')} · {post.get('when','')[:10]} · {post.get('url','')}"
        )

    out += ["", "## المصطلحات الأكثر تكراراً", "", "```"]
    out.append(" · ".join(f"{w}({c})" for w, c in terms.most_common(45)))
    out.append("```")

    Path("digest").mkdir(exist_ok=True)
    out_path = Path("digest") / f"x-history-{days}d.md"
    out_path.write_text("\n".join(out), encoding="utf-8")
    print(f"[analyze] wrote {out_path}")
    return 0


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    raise SystemExit(main(days))
