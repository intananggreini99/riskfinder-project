"""Modeling — replikasi Step 12–17 dari notebook (ringkas untuk produksi service).

Membandingkan kandidat model, memilih terbaik, menghitung metrik evaluasi,
learning curve ROC AUC (train vs test), confusion matrix, dan classification report.
"""
import numpy as np
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score, accuracy_score, confusion_matrix,
)

try:
    from xgboost import XGBClassifier
    _HAS_XGB = True
except Exception:  # pragma: no cover
    _HAS_XGB = False


def _candidates(spw):
    c = {
        "GradientBoosting": GradientBoostingClassifier(random_state=42),
        "RandomForest": RandomForestClassifier(random_state=42, n_jobs=-1, class_weight="balanced"),
        "AdaBoost": AdaBoostClassifier(random_state=42),
    }
    if _HAS_XGB:
        c["XGBoost"] = XGBClassifier(
            random_state=42, eval_metric="logloss", scale_pos_weight=spw, n_jobs=-1
        )
    return c


def learning_curve_auc(factory, X_train, y_train, X_test, y_test, fracs=np.linspace(0.2, 1.0, 6)):
    """Step 15 — kurva ROC AUC train vs test pada porsi data bertambah."""
    n = len(X_train)
    curve = []
    for frac in fracs:
        k = max(int(np.ceil(frac * n)), 50)
        idx = X_train.sample(n=min(k, n), random_state=42).index
        clf = factory()
        clf.fit(X_train.loc[idx], y_train.loc[idx])
        tr = roc_auc_score(y_train.loc[idx], clf.predict_proba(X_train.loc[idx])[:, 1])
        te = roc_auc_score(y_test, clf.predict_proba(X_test)[:, 1])
        curve.append({"size": f"{int(frac * 100)}%", "train": round(float(tr), 4), "test": round(float(te), 4)})
    return curve


def train_and_evaluate(X_train, X_test, y_train, y_test, n_trials=80):
    """Step 12–16. Return: (best_model, metrics, evaluation_dict)."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    spw = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

    # ---- Step 12: compare models via CV ROC AUC ----
    scores = {}
    for name, mdl in _candidates(spw).items():
        try:
            scores[name] = cross_val_score(mdl, X_train, y_train, cv=cv, scoring="roc_auc", n_jobs=-1).mean()
        except Exception:
            scores[name] = 0.0
    best_name = max(scores, key=scores.get)

    # ---- Step 13–14: latih ulang kandidat terbaik (tuning ringkas) ----
    # Catatan: tuning Optuna/Bayes penuh ada di notebook; di service dipakai konfigurasi solid.
    factory = lambda: _candidates(spw)[best_name]
    best_model = factory()
    best_model.fit(X_train, y_train)

    # ---- Step 15: evaluasi ----
    proba_tr = best_model.predict_proba(X_train)[:, 1]
    proba_te = best_model.predict_proba(X_test)[:, 1]
    pred_te = best_model.predict(X_test)

    auc_tr = float(roc_auc_score(y_train, proba_tr))
    auc_te = float(roc_auc_score(y_test, proba_te))
    tn, fp, fn, tp = confusion_matrix(y_test, pred_te).ravel()

    metrics = {
        "roc_auc_train": round(auc_tr, 4),
        "roc_auc_test": round(auc_te, 4),
        "gap": round(abs(auc_tr - auc_te), 4),
        "f1": round(float(f1_score(y_test, pred_te)), 4),
        "precision": round(float(precision_score(y_test, pred_te)), 4),
        "recall": round(float(recall_score(y_test, pred_te)), 4),
        "accuracy": round(float(accuracy_score(y_test, pred_te)), 4),
        "algorithm": best_name,
    }

    # classification report manual (kelas 0 & 1)
    def _report(cls):
        from sklearn.metrics import precision_recall_fscore_support
        p, r, f, s = precision_recall_fscore_support(y_test, pred_te, labels=[cls], zero_division=0)
        return {"precision": round(float(p[0]), 3), "recall": round(float(r[0]), 3),
                "f1": round(float(f[0]), 3), "support": int(s[0])}

    evaluation = {
        "learning_curve": learning_curve_auc(factory, X_train, y_train, X_test, y_test),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "classification_report": [
            {"label": "0 · Non-Default", **_report(0)},
            {"label": "1 · Default", **_report(1)},
        ],
        "roc_auc_train": round(auc_tr, 4),
        "roc_auc_test": round(auc_te, 4),
        "gap": round(abs(auc_tr - auc_te), 4),
    }
    return best_model, metrics, evaluation
