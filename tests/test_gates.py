from radar.sources.google_news import _topic_gate, looks_like_tech_post


def test_topic_gate_rejects_finance_benchmark():
    assert not _topic_gate("research", "The Bank of Canada raised its benchmark interest rate")
    assert _topic_gate("research", "New paper: agentic RAG for faithful reasoning")


def test_topic_gate_passes_non_gated_topics():
    assert _topic_gate("ai", "anything at all")


def test_writing_gate():
    assert _topic_gate("writing", "Typst 0.14 ships a faster math layout")
    assert not _topic_gate("writing", "A new phone was announced today")


def test_reasoning_gate():
    assert _topic_gate("reasoning", "Test-time compute scaling for verifiers")
    assert not _topic_gate("reasoning", "The weather is nice today in Baghdad")


def test_learning_gate():
    assert _topic_gate("learning", "Spaced repetition beats rereading in a new study")
    assert not _topic_gate("learning", "A new laptop review")


def test_promo_posts_are_rejected():
    assert not looks_like_tech_post("Check out our new API, sign up now and get credits for your model")
