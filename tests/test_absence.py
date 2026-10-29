from datetime import datetime, timedelta, timezone

from radar import archive
from radar.catchup import Item, _cluster
from radar.models import Signal
from radar.rank import Story
from radar.seen import SeenSet


def _story(title, url, score=50.0, source="x", taste=0.8):
    sig = Signal(
        title=title,
        url=url,
        source=source,
        published=datetime.now(timezone.utc),
        engagement=0,
    )
    sig.meta["taste"] = taste
    story = Story(lead=sig)
    story.score = score
    story.taste = taste
    return story


def test_seen_roundtrip(tmp_path):
    path = str(tmp_path / "seen.json")
    sig = Signal(
        title="OpenAI ships a model",
        url="https://a.com/1",
        source="x",
        published=datetime.now(timezone.utc),
    )
    seen = SeenSet(path)
    assert not seen.is_seen(sig)
    seen.mark(sig)
    seen.save()

    again = SeenSet(path)
    assert again.is_seen(sig)
    assert len(again) == 1


def test_seen_caps_growth(tmp_path):
    path = str(tmp_path / "seen.json")
    seen = SeenSet(path, cap=3)
    for i in range(6):
        seen.mark(_story(f"story {i}", f"https://a.com/{i}").lead)
    seen.save()
    assert len(SeenSet(path)) == 3


def test_archive_append_and_load(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, "ARCHIVE_DIR", str(tmp_path / "archive"))
    now = datetime.now(timezone.utc)
    archive.append([_story("Expo SDK 58 ships", "https://a.com/expo")], now)
    archive.append([_story("Expo SDK 58 ships", "https://a.com/expo")], now)  # duplicate

    rows = archive.load_range(2, now=now)
    assert len(rows) == 1
    assert rows[0]["title"] == "Expo SDK 58 ships"


def test_archive_prune(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, "ARCHIVE_DIR", str(tmp_path / "archive"))
    now = datetime.now(timezone.utc)
    archive.append([_story("old", "https://a.com/old")], now - timedelta(days=400))
    archive.append([_story("new", "https://a.com/new")], now)
    removed = archive.prune(keep_months=12, now=now)
    assert removed == 1
    assert len(archive.load_range(30, now=now)) == 1


def _row(title, score, day, sources=("x",)):
    return {
        "title": title,
        "url": f"https://a.com/{abs(hash(title))}",
        "score": score,
        "taste": 0.8,
        "topic": "ai",
        "sources": list(sources),
        "topics": ["ai"],
        "saved_at": f"{day}T06:00:00+00:00",
    }


def test_cluster_groups_repeats_and_counts_days():
    rows = [
        _row("OpenAI releases GPT-6 Astra with computer use", 55, "2026-10-01"),
        _row("OpenAI releases GPT-6 Astra with computer use", 60, "2026-10-03"),
        _row("Completely different chip shortage story", 40, "2026-10-02"),
    ]
    items = _cluster(rows)
    assert len(items) == 2
    top = max(items, key=lambda i: i.rank_score)
    assert len(top.days) == 2
    assert top.max_score == 60


def test_longevity_beats_single_day_spike():
    repeated = Item(title="keeps coming back", url="u1", max_score=40)
    repeated.days = {"d1", "d2", "d3", "d4"}
    spike = Item(title="one day spike", url="u2", max_score=45)
    spike.days = {"d1"}
    assert repeated.rank_score > spike.rank_score
