import gzip
import json

from radar import archive, summarize
from radar.catchup import _cluster, localize_records


def test_catchup_items_keep_archive_ids_for_stable_detail_urls():
    items = _cluster(
        [
            {
                "id": "stable-story-id",
                "title": "A persistent technology story",
                "url": "https://example.test/story",
                "score": 5,
                "sources": ["news"],
            }
        ]
    )

    assert items[0].to_dict()["id"] == "stable-story-id"


def test_localize_records_updates_rows_and_backfills_archive(monkeypatch):
    row = {
        "id": "archive-story-id",
        "title": "New tools improve Python startup",
        "url": "https://example.test/python-startup",
        "sources": ["x_account"],
        "topic": "dev",
        "score": 24,
    }
    duplicate = dict(row)
    persisted = {}

    def fake_summarize(stories, limit):
        assert limit == 1
        return {
            stories[0].lead.id: {"title_ar": "أدوات تسرّع بدء بايثون", "ar": "تحسّن الأدوات وقت بدء بايثون."}
        }

    monkeypatch.setattr(summarize, "summarize", fake_summarize)
    monkeypatch.setattr(archive, "update_localizations", lambda values: persisted.update(values))

    assert localize_records([row, duplicate]) == 1
    assert row["title_ar"] == "أدوات تسرّع بدء بايثون"
    assert duplicate["title_ar"] == "أدوات تسرّع بدء بايثون"
    assert persisted["archive-story-id"]["ar"] == "تحسّن الأدوات وقت بدء بايثون."


def test_archive_update_localizations_backfills_existing_row(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, "ARCHIVE_DIR", str(tmp_path))
    path = tmp_path / "2026-11.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as output:
        output.write(json.dumps({"id": "story-1", "title_ar": "", "ar": ""}) + "\n")

    assert archive.update_localizations(
        {"story-1": {"title_ar": "عنوان عربي", "ar": "شرح عربي"}}
    ) == 1
    row = archive.load_ids(path)[0]
    assert row["title_ar"] == "عنوان عربي"
    assert row["ar"] == "شرح عربي"
