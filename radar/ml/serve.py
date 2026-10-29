"""Pure-python scoring for the exported taste model.

No scikit-learn, no numpy: the JSON export is a term -> weight table plus a
small linear head, so the radar can score a tweet on any machine.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from .text import ngrams, shape_features


class TasteModel:
    def __init__(self, payload: dict) -> None:
        self.threshold = float(payload.get("threshold", 0.5))
        self.intercept = float(payload["intercept"])
        self.idf = payload["idf"]
        self.coef_text = payload["coef_text"]
        self.shape_keys = payload["shape_keys"]
        self.shape_mean = payload["shape_mean"]
        self.shape_std = payload["shape_std"]
        self.coef_shape = payload["coef_shape"]
        self.metrics = payload.get("metrics", {})

        # term -> (index, idf) so scoring never touches the vocab twice
        self.terms = {
            term: (int(idx), float(self.idf[int(idx)]))
            for term, idx in payload["vocab"].items()
            if int(idx) < len(self.idf)
        }
        self.top_positive = payload.get("top_positive", [])
        self.top_negative = payload.get("top_negative", [])

    @classmethod
    def load(cls, path: str = "data/taste_model.json") -> "TasteModel | None":
        p = Path(path)
        if not p.exists():
            return None
        return cls(json.loads(p.read_text("utf-8")))

    def _vector(self, text: str) -> list[tuple[str, float]]:
        counts = Counter(ngrams(text))
        vec: list[tuple[str, float]] = []
        for term, count in counts.items():
            hit = self.terms.get(term)
            if not hit:
                continue
            idx, idf = hit
            tf = 1.0 + math.log(count)  # sublinear tf
            vec.append((term, tf * idf, self.coef_text[idx]))
        return vec

    def score(self, text: str) -> float:
        vec = self._vector(text)
        if not vec:
            return 0.0
        norm = math.sqrt(sum((v * v) for _, v, _ in vec)) or 1.0
        dot = sum((tf * coef) for _, tf, coef in vec) / norm

        shape = shape_features(text)
        for key, mu, sd, coef in zip(
            self.shape_keys, self.shape_mean, self.shape_std, self.coef_shape
        ):
            dot += ((shape[key] - mu) / (sd or 1.0)) * coef

        z = dot + self.intercept
        z = max(-30.0, min(30.0, z))
        return 1.0 / (1.0 + math.exp(-z))

    def explain(self, text: str, k: int = 6) -> list[tuple[str, float]]:
        vec = self._vector(text)
        if not vec:
            return []
        norm = math.sqrt(sum((v * v) for _, v, _ in vec)) or 1.0
        contrib = [(term, (tf * coef) / norm) for term, tf, coef in vec]
        contrib.sort(key=lambda kv: abs(kv[1]), reverse=True)
        return [(t, round(c, 3)) for t, c in contrib[:k]]


def score_many(texts: list[str], payload: dict) -> list[float]:
    model = TasteModel(payload)
    return [model.score(t) for t in texts]
