"""CLI entry point.

    python main.py                 # collect, rank, write digest/
    python main.py --no-ai         # skip the Groq summaries
    python main.py --publish       # also send the top stories to Telegram
    python main.py --retro 60      # look back N days instead of the last 2

Designed to run unattended in GitHub Actions: no keys required, every source
fails soft, and the only side effects are files under digest/ and data/.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from radar import config
from radar.models import Signal
from radar.publish import enabled as telegram_enabled
from radar.publish import publish as telegram_publish
from radar.rank import Story, rank
from radar.render import write_outputs
from radar.sources import collect_all
from radar.store import Store
from radar.summarize import summarize


def _load_dotenv() -> None:
    """Read a local .env without adding a dependency."""
    path = Path(".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _dedupe(signals: list[Signal]) -> list[Signal]:
    seen: set[str] = set()
    out: list[Signal] = []
    for sig in signals:
        if not sig.title or not sig.url or sig.id in seen:
            continue
        seen.add(sig.id)
        out.append(sig)
    return out


def _apply_taste(signals: list[Signal], min_taste: float | None = None) -> list[Signal]:
    from radar.ml.serve import TasteModel

    model = TasteModel.load(config.TASTE_MODEL_PATH)
    if model is None:
        print("[taste] no model found — running without it")
        return signals

    floor = config.TASTE_MIN_PROB if min_taste is None else min_taste
    kept: list[Signal] = []
    dropped = 0
    for sig in signals:
        p = model.score(f"{sig.title}. {sig.summary or ''}")
        sig.meta["taste"] = round(p, 4)
        # X gets the hard floor; other sources are only filtered when they are
        # clearly off-topic, because the model was trained on this account.
        limit = floor if sig.source == "x" else floor * 0.6
        if p < limit:
            dropped += 1
            continue
        kept.append(sig)

    print(f"[taste] scored {len(signals)}, dropped {dropped} below p={floor:.2f}")
    return kept


def run(*, include_x: bool = True, use_ai: bool = True, do_publish: bool = False,
        top: int | None = None, fresh_only: bool = True, use_taste: bool = True,
        min_taste: float | None = None) -> list[Story]:
    print("[radar] collecting…")
    signals = _dedupe(collect_all(include_x=include_x))
    print(f"[radar] {len(signals)} signals")

    if use_taste:
        signals = _apply_taste(signals, min_taste)

    store = Store(config.DB_PATH)
    if fresh_only:
        before = len(signals)
        signals = [s for s in signals if not store.is_seen(s)]
        print(f"[radar] {len(signals)} new ({before - len(signals)} already shown)")

    stories = rank(signals, top_n=top or config.TOP_N)
    print(f"[radar] {len(stories)} stories")

    summaries = summarize(stories) if use_ai else {}
    md_path, json_path = write_outputs(
        stories,
        summaries=summaries,
        fetched=len(signals),
        digest_dir=config.DIGEST_DIR,
        data_dir=config.DATA_DIR,
    )
    print(f"[radar] wrote {md_path} and {json_path}")

    for story in stories:
        for member in story.members:
            store.mark_seen(member)
    store.log_run(
        len(signals), len(stories), stories[0].score if stories else 0.0
    )
    store.close()

    if do_publish:
        if telegram_enabled():
            telegram_publish(stories)
        else:
            print("[radar] --publish given but TELEGRAM_* is not set")

    return stories


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Free tech trend radar")
    parser.add_argument("--no-x", action="store_true", help="skip the X queries")
    parser.add_argument("--no-ai", action="store_true", help="skip Groq summaries")
    parser.add_argument("--no-taste", action="store_true", help="ignore the taste model")
    parser.add_argument(
        "--min-taste",
        type=float,
        default=None,
        help="drop X posts below this probability (default: config)",
    )
    parser.add_argument("--publish", action="store_true", help="send to Telegram")
    parser.add_argument("--top", type=int, default=config.TOP_N)
    parser.add_argument(
        "--all", action="store_true", help="include stories already shown before"
    )
    parser.add_argument(
        "--retro", type=int, metavar="DAYS", help="retrospective mode (see radar.retro)"
    )
    args = parser.parse_args(argv)

    _load_dotenv()

    if args.retro:
        from radar.retro import retro_report

        retro_report(days=args.retro)
        return 0

    stories = run(
        include_x=not args.no_x,
        use_ai=not args.no_ai,
        do_publish=args.publish,
        top=args.top,
        fresh_only=not args.all,
        use_taste=not args.no_taste,
        min_taste=args.min_taste,
    )
    if not stories:
        print("[radar] nothing new — try --all")
    return 0


if __name__ == "__main__":
    sys.exit(main())
