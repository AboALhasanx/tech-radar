from radar.catchup import _cluster


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
