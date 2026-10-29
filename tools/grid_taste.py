"""Small grid search for the taste model. Diagnostic only."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore")

from radar.ml.data import build  # noqa: E402
from radar.ml.text import ngrams, shape_features  # noqa: E402

SHAPE_KEYS = ["len_log", "has_code", "has_version", "has_percent", "has_benchmark", "has_arabic", "n_links", "n_lines"]

examples = build()
texts = [e.text for e in examples]
y = np.array([e.label for e in examples])
tr, te, ytr, yte = train_test_split(texts, y, test_size=0.2, random_state=7, stratify=y)

S = np.array([[shape_features(t)[k] for k in SHAPE_KEYS] for t in tr])
S2 = np.array([[shape_features(t)[k] for k in SHAPE_KEYS] for t in te])
mu, sd = S.mean(0), S.std(0)
sd[sd == 0] = 1
S = (S - mu) / sd
S2 = (S2 - mu) / sd

rows = []
for min_df in (1, 2):
    for max_features in (40000, 120000):
        vec = TfidfVectorizer(analyzer=ngrams, min_df=min_df, max_features=max_features,
                              sublinear_tf=True, norm="l2")
        T, T2 = vec.fit_transform(tr), vec.transform(te)
        X = hstack([T, csr_matrix(S)]).tocsr()
        X2 = hstack([T2, csr_matrix(S2)]).tocsr()
        for C in (0.3, 1, 3, 10, 30):
            for cw in ("balanced", None):
                clf = LogisticRegression(C=C, class_weight=cw, solver="liblinear", max_iter=3000)
                clf.fit(X, ytr)
                p = clf.predict_proba(X2)[:, 1]
                auc = roc_auc_score(yte, p)
                ap = average_precision_score(yte, p)
                rows.append((ap, auc, min_df, max_features, C, cw, len(vec.vocabulary_)))

rows.sort(reverse=True)
print(f"{'AP':>6} {'AUC':>6}  min_df  max_feat   C     class_weight   vocab")
for ap, auc, md, mf, c, cw, v in rows[:15]:
    print(f"{ap:6.3f} {auc:6.3f}  {md:>6}  {mf:>8}  {c:<4}  {str(cw):<12}  {v}")
