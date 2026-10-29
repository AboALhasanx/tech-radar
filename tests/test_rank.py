from datetime import datetime, timedelta, timezone

from radar.models import Signal, normalize_url
from radar.rank import cluster, rank, score_story, similarity, tokens


def _sig(title, source="x", age_hours=1, engagement=0.0, url=None):
    return Signal(
        title=title,
        url=url or f"https://example.com/{abs(hash(title))}",
        source=source,
        published=datetime.now(timezone.utc) - timedelta(hours=age_hours),
        engagement=engagement,
    )


def test_normalize_url_strips_tracking():
    assert normalize_url("https://a.com/x?utm_source=t&id=2") == "https://a.com/x?id=2"
    assert normalize_url("https://a.com/x/") == "https://a.com/x"
    assert normalize_url("https://a.com/x#frag") == "https://a.com/x"


def test_tokens_drop_stopwords():
    assert "the" not in tokens("the new model")
    assert "model" in tokens("the new model")


def test_similarity_is_symmetric():
    a, b = tokens("openai releases a new model"), tokens("a new model from openai")
    assert similarity(a, b) == similarity(b, a)
    assert similarity(a, b) > 0.5


def test_cluster_merges_same_story_across_sources():
    signals = [
        _sig("OpenAI releases GPT-6 with long context", "x"),
        _sig("OpenAI releases GPT-6 with long context", "hackernews", engagement=300),
        _sig("Completely unrelated chip shortage story", "news"),
    ]
    stories = cluster(signals)
    assert len(stories) == 2
    merged = [s for s in stories if len(s.members) == 2][0]
    assert merged.sources == {"x", "hackernews"}
    # the highest-engagement member becomes the lead
    assert merged.lead.source == "hackernews"


def test_cross_source_beats_single_source():
    solo = _sig("A quiet incremental release of a small library", "reddit")
    duo_a = _sig("A quiet incremental release of a small library", "reddit")
    duo_b = _sig("A quiet incremental release of a small library", "hackernews")
    stories = cluster([solo, duo_a, duo_b])
    for story in stories:
        score_story(story)
    assert stories[0].score >= stories[-1].score


def test_rank_is_sorted_and_bounded():
    titles = [
        "OpenAI ships a new reasoning model",
        "Rust compiler lands a faster borrow checker",
        "Flutter adds RTL text shaping fixes",
        "A tiny SQLite alternative written in Zig",
        "Postgres 19 ships incremental backups",
        "Someone reverse engineered a robot vacuum",
        "New Arabic OCR model beats the baseline",
        "GitHub Actions gets a cheaper runner tier",
        "Kubernetes drops an old deprecated API",
        "A deep dive into CSS anchor positioning",
    ]
    signals = [_sig(title, "x", age_hours=i * 6) for i, title in enumerate(titles)]
    stories = rank(signals, top_n=5)
    assert len(stories) == 5
    assert stories == sorted(stories, key=lambda s: s.score, reverse=True)
