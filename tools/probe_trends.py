"""Print what X actually renders on the trends routes (diagnostic)."""

from __future__ import annotations

import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from x_session import EXE, clone_profile, _text  # noqa: E402

from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

URLS = [
    "https://x.com/explore/tabs/trending",
    "https://x.com/explore",
    "https://x.com/home",
]

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(clone_profile()),
        executable_path=str(EXE),
        headless=True,
        viewport={"width": 1280, "height": 900},
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    for url in URLS:
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        main = page.query_selector("main") or page.query_selector("body")
        body = _text(main) if main else ""
        print(f"\n=== {url} (len={len(body)}) ===")
        print(body[:1200])
    ctx.close()

