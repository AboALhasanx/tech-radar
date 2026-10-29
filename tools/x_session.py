"""Read the logged-in X account through Thorium's default profile.

The browser is open, so the profile is locked. We copy only the pieces that
carry the session (Local State + the cookie jar) into a throwaway profile and
launch Thorium against that. Nothing is written back to the real profile.

Usage:
    python tools/x_session.py following
    python tools/x_session.py trends
    python tools/x_session.py timeline
"""

from __future__ import annotations

import json
import os
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LOCAL = Path(os.environ["LOCALAPPDATA"])
SRC = LOCAL / "Thorium" / "User Data"
EXE = LOCAL / "Thorium" / "Application" / "thorium.exe"
OUT = Path(__file__).resolve().parent.parent / "data"
HANDLE = "ab0_alhasan_"


def _copy_locked(src: Path, dst: Path) -> None:
    """Copy a file another process holds open (WinError 32 workaround)."""
    import ctypes
    import ctypes.wintypes as wt

    GENERIC_READ = 0x80000000
    SHARE_ALL = 0x01 | 0x02 | 0x04
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID = ctypes.c_void_p(-1).value

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.restype = ctypes.c_void_p
    k32.CreateFileW.argtypes = [
        wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.c_void_p, wt.DWORD, wt.DWORD, ctypes.c_void_p,
    ]
    handle = k32.CreateFileW(
        str(src), GENERIC_READ, SHARE_ALL, None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None
    )
    if handle == INVALID or handle is None:
        raise OSError(f"cannot open {src}: {ctypes.get_last_error()}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(dst, "wb") as out:
            buf = ctypes.create_string_buffer(1 << 20)
            read = wt.DWORD(0)
            while True:
                ok = k32.ReadFile(handle, buf, len(buf), ctypes.byref(read), None)
                if not ok or read.value == 0:
                    break
                out.write(buf.raw[: read.value])
    finally:
        k32.CloseHandle(handle)


def clone_profile() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="x-profile-"))
    (tmp / "Default" / "Network").mkdir(parents=True, exist_ok=True)
    for rel in (
        "Local State",
        "Default/Network/Cookies",
        "Default/Network/Cookies-journal",
        "Default/Preferences",
    ):
        src = SRC / rel
        if src.exists():
            try:
                _copy_locked(src, tmp / rel)
            except OSError as exc:
                print(f"[x] could not copy {rel}: {exc}")
    return tmp


def _text(el) -> str:
    try:
        return (el.inner_text() or "").strip()
    except Exception:
        return ""


def scrape_following(page, limit: int = 400) -> list[dict]:
    seen: dict[str, dict] = {}
    stagnant = 0
    for _ in range(60):
        cells = page.query_selector_all('[data-testid="UserCell"]')
        before = len(seen)
        for cell in cells:
            lines = [ln.strip() for ln in _text(cell).splitlines() if ln.strip()]
            handle = next((ln for ln in lines if ln.startswith("@")), "")
            if not handle:
                continue
            name = lines[0] if lines and not lines[0].startswith("@") else ""
            bio = " ".join(ln for ln in lines[1:] if not ln.startswith("@") and ln != name)
            seen[handle] = {"handle": handle, "name": name, "bio": bio[:240]}
        if len(seen) >= limit:
            break
        stagnant = stagnant + 1 if len(seen) == before else 0
        if stagnant >= 4:
            break
        page.mouse.wheel(0, 2400)
        page.wait_for_timeout(1200)
    return list(seen.values())


def scrape_trends(page) -> list[str]:
    page.goto("https://x.com/explore/tabs/trending", wait_until="domcontentloaded")
    page.wait_for_timeout(7000)

    out: list[str] = []
    for sel in ('[data-testid="trend"]', '[aria-label*="Trending"] [role="link"]'):
        for cell in page.query_selector_all(sel):
            txt = _text(cell)
            if txt and len(txt) > 3:
                out.append(txt.replace("\n", " | ")[:200])
        if out:
            return out

    # 2026 layout: the trend name is the line after "Category · Trending".
    main = page.query_selector("main") or page.query_selector("body")
    lines = [ln.strip() for ln in (_text(main) if main else "").splitlines() if ln.strip()]
    for i, line in enumerate(lines):
        if "·" in line and line.rstrip().endswith("Trending") and i + 1 < len(lines):
            name = lines[i + 1]
            if name in ("Trending", "Explore", "See new posts"):
                continue
            category = line.split("·")[0].strip()
            entry = f"{category}: {name}"
            if entry not in out:
                out.append(entry[:200])
    return out


def scrape_timeline(page, max_posts: int = 60) -> list[dict]:
    page.goto("https://x.com/home", wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    posts: list[dict] = []
    seen: set[str] = set()
    stagnant = 0
    for _ in range(40):
        for art in page.query_selector_all('article[data-testid="tweet"]'):
            txt = _text(art)
            if not txt or txt[:80] in seen:
                continue
            seen.add(txt[:80])
            posts.append({"text": txt.replace("\n", " ")[:400]})
        if len(posts) >= max_posts:
            break
        stagnant = stagnant + 1 if len(posts) < max_posts and not posts else 0
        page.mouse.wheel(0, 2200)
        page.wait_for_timeout(1400)
        if stagnant >= 6:
            break
    return posts[:max_posts]


def _collect_posts(page, max_posts: int, scrolls: int) -> list[dict]:
    posts: list[dict] = []
    seen: set[str] = set()
    for _ in range(scrolls):
        for art in page.query_selector_all('article[data-testid="tweet"]'):
            url_el = art.query_selector('a[href*="/status/"]')
            href = url_el.get_attribute("href") if url_el else ""
            if not href:
                continue
            url = href if href.startswith("http") else "https://x.com" + href
            if url in seen:
                continue
            seen.add(url)

            author_el = art.query_selector('[data-testid="User-Name"]')
            author = _text(author_el).replace("\n", " ")[:80] if author_el else ""

            text_el = art.query_selector('[data-testid="tweetText"]')
            text = _text(text_el) if text_el else ""

            time_el = art.query_selector("time[datetime]")
            when = time_el.get_attribute("datetime") if time_el else ""

            like_el = art.query_selector('[data-testid="like"]')
            likes = _text(like_el) if like_el else "0"

            posts.append(
                {
                    "url": url,
                    "author": author,
                    "text": text,
                    "when": when,
                    "likes": likes,
                }
            )
            if len(posts) >= max_posts:
                return posts
        page.mouse.wheel(0, 2200)
        page.wait_for_timeout(1400)
    return posts


def scrape_search(page, query: str, *, max_posts: int = 30, scrolls: int = 4) -> list[dict]:
    url = "https://x.com/search?q=" + quote(query, safe="") + "&f=top"
    try:
        page.goto(url, wait_until="domcontentloaded")
    except Exception as exc:
        print(f"[x] search failed: {str(exc).splitlines()[0]}")
        return []
    page.wait_for_timeout(4500)
    body = _text(page.query_selector("main") or page.query_selector("body"))
    if "No results for" in body:
        return []
    if "rate limit" in body.lower() or "try again" in body.lower():
        print("[x] rate limited")
        return []
    return _collect_posts(page, max_posts, scrolls)


def scrape_history(page, handles: list[str], days: int = 60, batch: int = 6) -> list[dict]:
    from datetime import datetime, timedelta, timezone

    until = datetime.now(timezone.utc) + timedelta(days=1)
    since = until - timedelta(days=days + 1)
    q_since, q_until = since.strftime("%Y-%m-%d"), until.strftime("%Y-%m-%d")

    batches = [handles[i : i + batch] for i in range(0, len(handles), batch)]
    print(f"[x] {len(handles)} accounts -> {len(batches)} search batches")

    all_posts: list[dict] = []
    seen: set[str] = set()

    for idx, group in enumerate(batches, 1):
        clause = " OR ".join(f"from:{h.lstrip('@')}" for h in group)
        query = f"({clause}) since:{q_since} until:{q_until}"
        posts = scrape_search(page, query, max_posts=30, scrolls=3)
        fresh = [p for p in posts if p["url"] not in seen]
        for p in fresh:
            seen.add(p["url"])
            p["batch"] = idx
        all_posts += fresh
        print(f"[x] {idx}/{len(batches)}: +{len(fresh)} (total {len(all_posts)})")

        if idx % 8 == 0:
            time.sleep(20)
        else:
            time.sleep(random.uniform(4.0, 7.0))

    return all_posts


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "following"
    headed = "--headed" in sys.argv
    tmp = clone_profile()
    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(tmp),
            executable_path=str(EXE),
            headless=not headed,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)

        try:
            page.goto(f"https://x.com/{HANDLE}", wait_until="domcontentloaded")
        except Exception as exc:
            print(f"[x] navigation failed: {str(exc).splitlines()[0]}")
            if not headed:
                print("[x] retrying headed…")
                ctx.close()
                return 3
            raise
        page.wait_for_timeout(4000)
        url = page.url
        print(f"[x] landed on {url}")

        if "/i/jf/onboarding" in url or "login" in url:
            print("[x] NOT logged in — profile cookies did not carry the session")
            ctx.close()
            return 2

        if mode == "following":
            page.goto(f"https://x.com/{HANDLE}/following", wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            data = scrape_following(page)
            path = OUT / "x_following.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[x] {len(data)} accounts -> {path}")
            for row in data[:15]:
                print(f"   {row['handle']:<24} {row['name'][:30]}")

        elif mode == "trends":
            data = scrape_trends(page)
            path = OUT / "x_trends.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[x] {len(data)} trends -> {path}")
            for t in data[:20]:
                print("   " + t[:120])

        elif mode == "timeline":
            data = scrape_timeline(page)
            path = OUT / "x_timeline.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[x] {len(data)} posts -> {path}")
            for post in data[:10]:
                print("   " + post["text"][:160])

        elif mode == "history":
            days = 60
            if "--days" in sys.argv:
                days = int(sys.argv[sys.argv.index("--days") + 1])
            limit = None
            if "--limit" in sys.argv:
                limit = int(sys.argv[sys.argv.index("--limit") + 1])

            following_path = OUT / "x_following.json"
            if not following_path.exists():
                print("[x] run 'following' first")
                ctx.close()
                return 4
            handles = [row["handle"] for row in json.loads(following_path.read_text("utf-8"))]
            if limit:
                handles = handles[:limit]

            data = scrape_history(page, handles, days=days)
            path = OUT / f"x_history_{days}d.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[x] {len(data)} posts -> {path}")

        ctx.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
