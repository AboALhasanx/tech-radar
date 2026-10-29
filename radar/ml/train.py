"""Train the taste model and export it as plain JSON.

Model
-----
    p(liked | post) = sigmoid( wÂ·tfidf(post) + uÂ·shape(post) + b )

* tf-idf: sublinear tf `1 + log(tf)`, smoothed idf `log((1+N)/(1+df)) + 1`,
  L2-normalised â€” the same definition scikit-learn uses, reimplemented at
  serve time so inference needs no dependency.
* shape: structural signals (has code, has version, has benchmark, â€¦)
  standardised with the training mean/std.
* logistic regression with balanced class weights, because likes are ~13% of
  the corpus and a model that always says "no" would look 87% accurate.

Everything is evaluated on a held-out split, and the export stores the
metrics so the radar can refuse to use a bad model.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

from .data import build, stats
from .text import ngrams, shape_features

SHAPE_KEYS = [
    "len_log",
    "has_code",
    "has_version",
    "has_percent",
    "has_benchmark",
    "has_arabic",
    "n_links",
    "n_lines",
]


def analyzer(text: str) -> list[str]:
    return ngrams(text)


def _parse_when(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def _shape_matrix(texts: list[str]) -> np.ndarray:
    return np.array(
        [[shape_features(t)[k] for k in SHAPE_KEYS] for t in texts], dtype=np.float64
    )


def _sig(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def train(*, out_path: str = "data/taste_model.json", seed: int = 7) -> dict:
    examples = build()
    info = stats(examples)
    print(f"[train] {info}")

    texts = [e.text for e in examples]
    y = np.array([e.label for e in examples])

    dated = [(e, _parse_when(e.when)) for e in examples]
    dated = [(e, d) for e, d in dated if d]
    if dated:
        span = max(d for _, d in dated) - min(d for _, d in dated)
        print(f"[train] dated examples: {len(dated)} over {span.days} days")

    X_text_train, X_text_test, y_train, y_test = train_test_split(
        texts, y, test_size=0.2, random_state=seed, stratify=y
    )

    vectorizer = TfidfVectorizer(
        analyzer=analyzer,
        min_df=1,
        max_features=40000,
        sublinear_tf=True,
        norm="l2",
        dtype=np.float64,
    )
    T_train = vectorizer.fit_transform(X_text_train)
    T_test = vectorizer.transform(X_text_test)

    S_train = _shape_matrix(X_text_train)
    S_test = _shape_matrix(X_text_test)
    mean = S_train.mean(axis=0)
    std = S_train.std(axis=0)
    std[std == 0] = 1.0
    S_train = (S_train - mean) / std
    S_test = (S_test - mean) / std

    X_train = hstack([T_train, csr_matrix(S_train)]).tocsr()
    X_test = hstack([T_test, csr_matrix(S_test)]).tocsr()

    clf = LogisticRegression(
        C=30.0,
        class_weight="balanced",
        solver="liblinear",
        max_iter=2000,
        random_state=seed,
    )
    clf.fit(X_train, y_train)

    proba = clf.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    ap = average_precision_score(y_test, proba)

    # threshold chosen on the holdout to maximise F1 for the positive class
    best = (0.5, 0.0)
    for t in np.linspace(0.05, 0.95, 91):
        pred = (proba >= t).astype(int)
        _, _, f1, _ = precision_recall_fscore_support(
            y_test, pred, average="binary", zero_division=0
        )
        if f1 > best[1]:
            best = (float(t), float(f1))
    threshold, f1 = best

    cv = cross_val_score(
        LogisticRegression(
            C=30.0, class_weight="balanced", solver="liblinear", max_iter=2000
        ),
        X_train,
        y_train,
        cv=StratifiedKFold(5, shuffle=True, random_state=seed),
        scoring="roc_auc",
    )

    pred_sorted = np.argsort(-proba)
    k = min(20, len(y_test))
    precision_at_k = float(y_test[pred_sorted[:k]].mean())

    print(f"[train] ROC-AUC={auc:.3f}  AP={ap:.3f}  F1={f1:.3f}  P@20={precision_at_k:.3f}")
    print(f"[train] 5-fold AUC={cv.mean():.3f} Â± {cv.std():.3f}")

    vocab = {term: int(idx) for term, idx in vectorizer.vocabulary_.items()}
    idf = vectorizer.idf_.tolist()
    coef_text = clf.coef_[0][: len(vocab)].tolist()
    coef_shape = clf.coef_[0][len(vocab) :].tolist()

    # top features, so the model can explain itself
    inv_vocab = {i: t for t, i in vocab.items()}
    order = np.argsort(-np.array(coef_text))
    top_pos = [(inv_vocab[i], round(float(coef_text[i]), 3)) for i in order[:30]]
    top_neg = [(inv_vocab[i], round(float(coef_text[i]), 3)) for i in order[-30:]]

    payload = {
        "version": 1,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "roc_auc": round(float(auc), 4),
            "average_precision": round(float(ap), 4),
            "f1": round(f1, 4),
            "precision_at_20": round(precision_at_k, 4),
            "cv_auc_mean": round(float(cv.mean()), 4),
            "cv_auc_std": round(float(cv.std()), 4),
            "n_total": info["total"],
            "n_positive": info["positive"],
            "n_negative": info["negative"],
        },
        "threshold": round(threshold, 3),
        "intercept": float(clf.intercept_[0]),
        "vocab": vocab,
        "idf": idf,
        "coef_text": coef_text,
        "shape_keys": SHAPE_KEYS,
        "shape_mean": mean.tolist(),
        "shape_std": std.tolist(),
        "coef_shape": [float(v) for v in coef_shape],
        "top_positive": top_pos,
        "top_negative": top_neg,
    }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"[train] wrote {out_path}")

    print("\n[train] what it learned to like:")
    for term, weight in top_pos[:18]:
        print(f"   +{weight:<7} {term}")
    print("\n[train] what it learned to skip:")
    for term, weight in top_neg[-12:][::-1]:
        print(f"   {weight:<8} {term}")
    return payload


def _self_check(payload: dict, texts: list[str]) -> None:
    """Confirm the pure-python scorer matches scikit-learn on a few samples."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    from .serve import score_many

    vec = TfidfVectorizer(
        analyzer=analyzer,
        min_df=1,
        max_features=40000,
        sublinear_tf=True,
        norm="l2",
        dtype=np.float64,
        vocabulary=payload["vocab"],
    )
    vec.idf_ = np.array(payload["idf"])
    T = vec.transform(texts)
    S = _shape_matrix(texts)
    mean = np.array(payload["shape_mean"])
    std = np.array(payload["shape_std"])
    S = (S - mean) / std
    w = np.array(payload["coef_text"])
    u = np.array(payload["coef_shape"])
    b = payload["intercept"]
    expected = 1 / (1 + np.exp(-(T @ w + S @ u + b)))
    got = np.array(score_many(texts, payload))
    delta = float(np.max(np.abs(expected - got)))
    print(f"[train] parity with sklearn: max |delta| = {delta:.2e}")


if __name__ == "__main__":
    payload = train()
    examples = build()
    _self_check(payload, [e.text for e in examples[:5]])


