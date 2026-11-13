import json
import struct
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

from radar import site, site_pwa


def _story(**overrides):
    story = {
        "id": "story-1",
        "title": "New Python tools arrive",
        "title_ar": "أدوات جديدة لبايثون",
        "ar": "تضيف الأدوات الجديدة وسائل أسرع لبناء التطبيقات.",
        "url": "https://example.test/python-tools",
        "sources": ["news"],
        "topic": "dev",
        "topics": ["dev"],
        "score": 42,
        "taste": 0.8,
    }
    story.update(overrides)
    return story


def test_site_builds_story_pages_and_installable_pwa(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "brief.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-11-14T06:00:00+00:00",
                "stories": [_story()],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    out = site.build(tmp_path / "site-output")

    index = (out / "index.html").read_text(encoding="utf-8")
    detail = (out / "stories" / "story-1.html").read_text(encoding="utf-8")
    markdown = (out / "downloads" / "story-1.md").read_text(encoding="utf-8")
    manifest = json.loads((out / "manifest.webmanifest").read_text(encoding="utf-8"))
    feed = ET.parse(out / "feed.xml")

    assert 'href="./stories/story-1.html"' in index
    assert "أدوات جديدة لبايثون" in index
    assert "أدوات جديدة لبايثون" in detail
    assert "تضيف الأدوات الجديدة" in detail
    assert 'href="https://example.test/python-tools"' in detail
    assert 'rel="noopener noreferrer"' in detail
    assert 'href="../downloads/story-1.md" download' in detail
    assert "[افتح الخبر الأصلي](https://example.test/python-tools)" in markdown
    assert manifest["display"] == "standalone"
    assert manifest["scope"] == "./"
    assert {icon["sizes"] for icon in manifest["icons"]} >= {"192x192", "512x512"}
    assert (out / "saved.html").exists()
    assert (out / "offline.html").exists()
    assert "SAVE_STORY" in (out / "sw.js").read_text(encoding="utf-8")
    assert struct.unpack(">II", (out / "icons" / "icon-192.png").read_bytes()[16:24]) == (192, 192)
    assert feed.findtext("./channel/item/title") == "أدوات جديدة لبايثون"
    last_build_date = feed.findtext("./channel/lastBuildDate")
    assert parsedate_to_datetime(last_build_date).year == 2026


def test_site_prefers_latest_story_localizations(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    story = _story()
    story.pop("title_ar")
    story.pop("ar")
    (data_dir / "brief.json").write_text(
        json.dumps({"stories": [story]}), encoding="utf-8"
    )
    (data_dir / "latest.json").write_text(
        json.dumps(
            {
                "stories": [
                    _story(title_ar="عنوان من أحدث تشغيل", ar="شرح من أحدث تشغيل")
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    loaded = site._load()

    assert loaded["stories"][0]["title_ar"] == "عنوان من أحدث تشغيل"
    assert loaded["stories"][0]["ar"] == "شرح من أحدث تشغيل"


def test_site_rejects_unsafe_source_schemes_and_escapes_titles(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "brief.json").write_text(
        json.dumps(
            {
                "stories": [
                    _story(
                        title='<img src=x onerror="alert(1)">',
                        title_ar="عنوان آمن",
                        url="javascript:alert(1)",
                    )
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    out = site.build(tmp_path / "site-output")
    detail = (out / "stories" / "story-1.html").read_text(encoding="utf-8")

    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in detail
    assert "javascript:" not in detail
    assert "href=\"https://example.test" not in detail


def test_site_prefers_latest_over_newer_brief_and_keeps_shelves(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "brief.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-11-13T21:50:34.730340+00:00",
                "stories": [_story(id="old-story")],
                "shelves": {"researchers": [_story(id="researcher-story")]},
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "latest.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-11-13T21:50:34.312985+00:00",
                "stories": [_story(id="new-story")],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    loaded = site._load()

    assert loaded["stories"][0]["id"] == "new-story"
    assert loaded["shelves"]["researchers"][0]["id"] == "researcher-story"



def test_service_worker_version_changes_when_shell_markup_changes(tmp_path):
    versions = []
    for index, markup in enumerate(("<h1>old</h1>", "<h1>new</h1>")):
        out = tmp_path / str(index)
        out.mkdir()
        for name in ("index.html", "saved.html", "offline.html"):
            content = markup if name == "index.html" else "<main>shell</main>"
            (out / name).write_text(content, encoding="utf-8")
        site_pwa.write_assets(out, "same-data-version")
        versions.append((out / "sw.js").read_text(encoding="utf-8"))

    assert versions[0] != versions[1]
