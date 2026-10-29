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

from radar import archive, config
from radar.models import Signal
from radar.publish import enabled as telegram_enabled
from radar.publish import ntfy_enabled, ntfy_send
from radar.publish import publish as telegram_publish
from radar.publish import publish_alert
from radar.rank import Story, rank
from radar.render import write_outputs
from radar.seen import SeenSet
from radar.sources import collect_all
from radar.summarize import summarize
from radar.watchlist import check as watch_check


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
        min_taste: float | None = None, do_alerts: bool = False) -> list[Story]:
    print("[radar] collecting…")
    signals = _dedupe(collect_all(include_x=include_x))
    print(f"[radar] {len(signals)} signals")

    if use_taste:
        signals = _apply_taste(signals, min_taste)

    seen = SeenSet(config.SEEN_PATH)
    if fresh_only:
        before = len(signals)
        signals = [s for s in signals if not seen.is_seen(s)]
        print(f"[radar] {len(signals)} new ({before - len(signals)} already shown)")

    # Rank deeper than the digest needs: the extra stories feed the archive and
    # the seen-set, so tomorrow's run does not serve the same fifteen links.
    ranked = rank(signals, top_n=max(120, top or 0))
    stories = ranked[: (top or config.TOP_N)]
    print(f"[radar] {len(stories)} stories ({len(ranked)} ranked)")

    summaries = summarize(stories) if use_ai else {}
    md_path, json_path = write_outputs(
        stories,
        summaries=summaries,
        fetched=len(signals),
        digest_dir=config.DIGEST_DIR,
        data_dir=config.DATA_DIR,
    )
    print(f"[radar] wrote {md_path} and {json_path}")

    # durable history for catch-up mode
    if ranked:
        extras = []
        for source, n in (("newsletter", 8), ("producthunt", 5)):
            subset = [s for s in signals if s.source == source]
            if subset:
                extras += rank(subset, top_n=n)
        merged: list[Story] = []
        seen_ids: set[str] = set()
        for story in ranked[:60] + extras:
            if story.lead.id in seen_ids:
                continue
            seen_ids.add(story.lead.id)
            merged.append(story)
        archive.append(merged)
        archive.prune()

    for story in ranked:
        for member in story.members:
            seen.mark(member)
    seen.save()
    print(f"[radar] seen set: {len(seen)} ids")

    if do_alerts:
        hits = watch_check(stories)
        if hits:
            for story, matched in hits[:4]:
                print(f"[alert] {story.lead.title[:60]} ({', '.join(matched[:3])})")
            if telegram_enabled():
                publish_alert(hits)
            if ntfy_enabled():
                lines = [f"• {s.lead.title[:120]} — {s.lead.url}" for s, _ in hits[:4]]
                ntfy_send("⚡ رادار: تنبيه", "\n".join(lines), priority="high", tags="zap")
        else:
            print("[alert] no watchlist matches")

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
    parser.add_argument(
        "--alerts", action="store_true", help="ping Telegram on watchlist matches"
    )
    parser.add_argument("--top", type=int, default=config.TOP_N)
    parser.add_argument(
        "--all", action="store_true", help="include stories already shown before"
    )
    parser.add_argument(
        "--retro", type=int, metavar="DAYS", help="retrospective mode (see radar.retro)"
    )
    parser.add_argument(
        "--catchup",
        type=int,
        metavar="DAYS",
        help="what you missed over the last N days (from the archive)",
    )
    parser.add_argument(
        "--every",
        type=int,
        metavar="DAYS",
        help="collect, archive, and publish a brief for the last N days",
    )
    parser.add_argument(
        "--weekly",
        action="store_true",
        help="weekly rollup + refresh CATCHUP.md",
    )
    args = parser.parse_args(argv)

    _load_dotenv()

    if args.retro:
        from radar.retro import retro_report

        retro_report(days=args.retro)
        return 0

    if args.catchup:
        from radar.catchup import write_report

        path = write_report(
            args.catchup, top=max(args.top, 25), use_ai=not args.no_ai
        )
        print(f"[radar] catch-up written to {path}")
        return 0

    if args.weekly:
        from datetime import datetime, timezone

        from radar.catchup import write_report, write_rolling
        from radar.publish import publish_catchup

        now = datetime.now(timezone.utc)
        year, week, _ = now.isocalendar()
        path = write_report(
            7,
            top=12,
            use_ai=not args.no_ai,
            out_path=f"{config.DIGEST_DIR}/weekly/{year}-W{week:02d}.md",
        )
        write_rolling(30, 30)
        if args.publish and telegram_enabled():
            publish_catchup(path.read_text("utf-8"))
        if ntfy_enabled():
            from radar.catchup import load_items

            items = load_items(7)
            top = "\n".join(f"• {i.title[:110]}" for i in items[:6])
            ntfy_send("📡 رادار: ملخص الأسبوع", top or "لا جديد", tags="newspaper")
        print(f"[radar] weekly written to {path}")
        return 0

    stories = run(
        include_x=not args.no_x,
        use_ai=not args.no_ai,
        do_publish=args.publish,
        top=args.top,
        fresh_only=not args.all,
        use_taste=not args.no_taste,
        min_taste=args.min_taste,
        do_alerts=args.alerts,
    )

    if args.every:
        from datetime import datetime, timezone

        from radar.catchup import write_report

        now = datetime.now(timezone.utc)
        path = write_report(
            args.every,
            top=max(args.top, 20),
            use_ai=not args.no_ai,
            out_path=f"{config.DIGEST_DIR}/brief-{now:%Y-%m-%d}.md",
        )
        print(f"[radar] {args.every}-day brief written to {path}")
    if not stories:
        print("[radar] nothing new — try --all")
    return 0


if __name__ == "__main__":
    sys.exit(main())
