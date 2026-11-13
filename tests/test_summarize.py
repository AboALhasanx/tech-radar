import json
from datetime import datetime, timezone

from radar import summarize as summarize_module
from radar.models import Signal
from radar.rank import Story


def _story():
    return Story(
        lead=Signal(
            title="A new Python release makes startup faster",
            url="https://example.test/python-release",
            source="news",
            topic="dev",
            published=datetime.now(timezone.utc),
            summary="The release includes interpreter startup improvements.",
        )
    )


def test_summarize_returns_arabic_title_and_explanation(monkeypatch):
    story = _story()
    monkeypatch.setenv("GROQ_API_KEY", "test-only")
    captured = {}

    def fake_post(url, payload, key):
        captured.update(url=url, payload=payload, key=key)
        content = {
            "items": [
                {
                    "id": story.lead.id,
                    "title_ar": "إصدار جديد من بايثون يسرّع بدء التشغيل",
                    "ar": "يتضمن الإصدار تحسينات تقلل وقت تشغيل المفسر.",
                }
            ]
        }
        return {"choices": [{"message": {"content": json.dumps(content, ensure_ascii=False)}}]}

    monkeypatch.setattr(summarize_module, "_post", fake_post)

    result = summarize_module.summarize([story])

    assert result[story.lead.id]["title_ar"].startswith("إصدار جديد")
    assert result[story.lead.id]["ar"].startswith("يتضمن الإصدار")
    assert captured["key"] == "test-only"
    prompt = captured["payload"]["messages"][0]["content"]
    assert "title_ar" in prompt
    assert "interpreter startup improvements" in prompt


def test_summarize_keeps_older_ar_only_response_compatible(monkeypatch):
    story = _story()
    monkeypatch.setenv("GROQ_API_KEY", "test-only")
    monkeypatch.setattr(
        summarize_module,
        "_post",
        lambda *args: {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {"items": [{"id": story.lead.id, "ar": "شرح عربي"}]}
                        )
                    }
                }
            ]
        },
    )

    assert summarize_module.summarize([story]) == {
        story.lead.id: {"title_ar": "", "ar": "شرح عربي"}
    }


def test_summarize_skips_api_without_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(
        summarize_module,
        "_post",
        lambda *args: (_ for _ in ()).throw(AssertionError("API should not be called")),
    )

    assert summarize_module.summarize([_story()]) == {}
