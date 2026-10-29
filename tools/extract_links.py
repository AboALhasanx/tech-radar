"""Extract concrete technical artefacts (repos, papers, posts) from the corpus."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

URL_RE = re.compile(r"https?://[^\s)>\"]+")


def domain(url: str) -> str:
    m = re.match(r"https?://(?:www\.)?([^/]+)", url)
    return (m.group(1) if m else "").lower()


def main() -> int:
    posts = json.loads(Path("data/x_history_60d.json").read_text("utf-8"))

    repo_counter: Counter = Counter()
    repo_posts: dict[str, dict] = defaultdict(dict)
    domain_counter: Counter = Counter()

    for post in posts:
        text = post.get("text") or ""
        for url in URL_RE.findall(text):
            url = url.rstrip(".,;")
            d = domain(url)
            if d:
                domain_counter[d] += 1
            if "github.com" in d:
                parts = url.split("github.com/")[-1].split("/")
                if len(parts) >= 2:
                    repo = f"{parts[0]}/{parts[1]}".strip()
                    if repo and not repo.startswith("."):
                        repo_counter[repo] += 1
                        repo_posts[repo] = post

    print("== top link domains ==")
    for d, c in domain_counter.most_common(25):
        print(f"{c:>4}  {d}")

    print("\n== github repos mentioned ==")
    for repo, c in repo_counter.most_common(40):
        post = repo_posts[repo]
        text = (post.get("text") or "").replace("\n", " ")[:200]
        print(f"{c:>3}  {repo:<45} {post.get('when','')[:10]}  {text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
