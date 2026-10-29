import json

from radar.ml.serve import TasteModel

PAYLOAD = {
    "threshold": 0.5,
    "intercept": -1.0,
    "vocab": {"agent": 0, "expo": 1, "travel": 2, "agent_expo": 3},
    "idf": [1.5, 1.8, 2.2, 2.6],
    "coef_text": [2.5, 2.0, -3.0, 1.0],
    "shape_keys": ["len_log", "has_code"],
    "shape_mean": [10.0, 0.1],
    "shape_std": [5.0, 0.3],
    "coef_shape": [0.2, 0.4],
    "top_positive": [["agent", 2.5]],
    "top_negative": [["travel", -3.0]],
}


def test_score_is_a_probability():
    model = TasteModel(PAYLOAD)
    for text in ("new agent framework", "travel vlog", "", "expo app release"):
        p = model.score(text)
        assert 0.0 <= p <= 1.0


def test_it_prefers_liked_vocabulary():
    model = TasteModel(PAYLOAD)
    assert model.score("agent framework") > model.score("travel vlog")


def test_explain_names_the_driving_terms():
    model = TasteModel(PAYLOAD)
    terms = [t for t, _ in model.explain("travel agent expo", k=3)]
    assert "travel" in terms


def test_empty_text_is_neutral():
    model = TasteModel(PAYLOAD)
    assert model.score("") == 0.0


def test_load_roundtrip(tmp_path):
    path = tmp_path / "m.json"
    path.write_text(json.dumps(PAYLOAD), encoding="utf-8")
    model = TasteModel.load(str(path))
    assert model is not None
    assert model.metrics == {}
    assert TasteModel.load(str(tmp_path / "missing.json")) is None
