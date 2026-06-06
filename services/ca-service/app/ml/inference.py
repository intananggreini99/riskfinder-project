"""Inference Credit Analysis — replikasi persis preprocess_for_inference (Step 18 notebook).

Memuat pasangan model+preprocessing aktif dari Docker Volume (ditunjuk active_pair.json,
ditulis oleh ds-service saat deploy). Bila tidak ada pointer, memakai file default.
"""
import json
import os
import threading

import joblib
import numpy as np
import pandas as pd

from ..config import settings

_lock = threading.Lock()
_cache = {"model": None, "artifacts": None, "model_file": None}


def _resolve_active_files():
    """Tentukan file model & preprocessing yang aktif (dari pointer atau default)."""
    model_file, prep_file = settings.DEFAULT_MODEL_FILE, settings.DEFAULT_PREP_FILE
    if os.path.exists(settings.ACTIVE_POINTER):
        try:
            with open(settings.ACTIVE_POINTER) as f:
                ptr = json.load(f)
            model_file = ptr.get("model_file") or model_file
            prep_file = ptr.get("preprocessing_file") or prep_file
        except Exception:
            pass
    return model_file, prep_file


def load_active(force: bool = False):
    """Muat (atau muat ulang) model & artifacts aktif, dengan caching."""
    with _lock:
        model_file, prep_file = _resolve_active_files()
        if not force and _cache["model"] is not None and _cache["model_file"] == model_file:
            return _cache["model"], _cache["artifacts"], model_file

        model_path = os.path.join(settings.MODEL_DIR, model_file)
        prep_path = os.path.join(settings.PREP_DIR, prep_file)
        if not (os.path.exists(model_path) and os.path.exists(prep_path)):
            raise FileNotFoundError(
                f"Artifact aktif belum tersedia di Docker Volume "
                f"({model_path} / {prep_path}). Pastikan Data Scientist sudah build & deploy model."
            )
        model = joblib.load(model_path)
        artifacts = joblib.load(prep_path)
        _cache.update({"model": model, "artifacts": artifacts, "model_file": model_file})
        return model, artifacts, model_file


def create_features(df_in: pd.DataFrame) -> pd.DataFrame:
    """Identik dengan feature extraction training (Step 7)."""
    df = df_in.copy()
    bill = [f"BILL_AMT{i}" for i in range(1, 7)]
    payamt = [f"PAY_AMT{i}" for i in range(1, 7)]
    delay = [f"PAY_{i}" for i in range(1, 7)]
    df["AVG_UTIL_RATIO"] = df[bill].div(df["LIMIT_BAL"] + 1, axis=0).mean(axis=1)
    df["AVG_PAY_AMT"] = df[payamt].mean(axis=1)
    df["N_LATE_PAYMENTS"] = (df[delay] > 0).sum(axis=1)
    df["MAX_DELAY"] = df[delay].max(axis=1)
    df["BILL_TREND"] = df["BILL_AMT1"] - df["BILL_AMT6"]
    df["PAY_AMT_STD"] = df[payamt].std(axis=1).fillna(0)
    return df


def preprocess_for_inference(df_raw: pd.DataFrame, artifacts: dict) -> pd.DataFrame:
    """Transformasi data mentah agar identik dengan pipeline training."""
    df = df_raw.copy()

    # 1) PAY_0 -> PAY_1
    if "PAY_0" in df.columns:
        df = df.rename(columns={"PAY_0": "PAY_1"})

    # 2) inkonsistensi EDUCATION/MARRIAGE -> fallback
    df["EDUCATION"] = df["EDUCATION"].apply(
        lambda x: artifacts["fallback_education"] if x in [0, 5, 6] else x
    ).astype(int)
    df["MARRIAGE"] = df["MARRIAGE"].apply(
        lambda x: artifacts["fallback_marriage"] if x == 0 else x
    ).astype(int)

    # 3) outlier capping (batas dari TRAIN)
    for col, (lower, upper) in artifacts["outlier_boundaries"].items():
        if col in df.columns:
            df[col] = np.clip(df[col], lower, upper)

    # 4) feature extraction (sama dengan training)
    df = create_features(df)

    # 5) AGE binning -> ordinal
    df["AGE_GROUP"] = (
        pd.cut(df["AGE"], bins=artifacts["age_bins"], labels=artifacts["age_labels"], right=False)
        .map(artifacts["age_group_mapping"])
        .astype(int)
    )

    # 6) OHE MARRIAGE
    df = pd.get_dummies(df, columns=["MARRIAGE"])
    for col in artifacts["marriage_ohe_columns"]:
        if col not in df.columns:
            df[col] = 0

    # 7) label encode SEX
    df["SEX"] = df["SEX"].map(artifacts["sex_mapping"]).astype(int)

    # 8) susun kolom final sesuai urutan training (kolom hilang -> 0)
    for col in artifacts["final_columns"]:
        if col not in df.columns:
            df[col] = 0
    df = df[artifacts["final_columns"]]

    # 9) scaling kolom kontinu
    df[artifacts["columns_to_stdscaler"]] = artifacts["scaler"].transform(
        df[artifacts["columns_to_stdscaler"]]
    )
    return df


def predict_one(raw: dict) -> dict:
    """Prediksi satu peminjam. Return label, score, status."""
    model, artifacts, model_file = load_active()
    X = preprocess_for_inference(pd.DataFrame([raw]), artifacts)

    proba = float(model.predict_proba(X)[:, 1][0])
    label = int(proba >= 0.5)
    # prediction_score = probabilitas kelas terprediksi (selaras PyCaret)
    score = proba if label == 1 else 1 - proba
    return {
        "prediction_label": label,
        "prediction_score": round(float(score), 4),
        "status": "Default" if label == 1 else "Non-Default",
        "_model_file": model_file,
    }
