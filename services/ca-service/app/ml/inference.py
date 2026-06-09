"""Inference Credit Analysis — kompatibel dengan artifact notebook
`Preprocessing_Modeling_EndToEnd_.ipynb`.

Model aktif dibaca dari Docker Volume `/artifacts`. Bila `active_pair.json` belum
ada, service memakai `best_credit_model_V1.pkl` dan
`preprocessing_artifacts_V1.pkl` sebagai fallback default.
"""
import json
import os
import threading
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from pycaret.classification import predict_model

from ..config import settings

_lock = threading.Lock()
_cache = {"model": None, "artifacts": None, "model_file": None, "prep_file": None}


def _seed_default_artifacts_if_needed() -> None:
    """Salin artifact bawaan image ke Docker Volume kosong saat lokal/docker-compose.

    Mount Docker Volume pada `/artifacts` akan menimpa file yang dibake ke image.
    Karena itu Dockerfile juga menaruh salinan pada `/seed-artifacts`; fungsi ini
    melakukan copy satu kali bila volume belum berisi V1.
    """
    seed_root = Path("/seed-artifacts")
    if not seed_root.exists():
        return
    for rel in (
        f"models/{settings.DEFAULT_MODEL_FILE}",
        f"preprocessing/{settings.DEFAULT_PREP_FILE}",
    ):
        src = seed_root / rel
        dst = Path(settings.ARTIFACT_DIR) / rel
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())


def _resolve_active_files():
    """Tentukan file model & preprocessing yang aktif (dari pointer atau default)."""
    model_file, prep_file = settings.DEFAULT_MODEL_FILE, settings.DEFAULT_PREP_FILE
    if os.path.exists(settings.ACTIVE_POINTER):
        try:
            with open(settings.ACTIVE_POINTER, encoding="utf-8") as f:
                ptr = json.load(f)
            model_file = ptr.get("model_file") or model_file
            prep_file = ptr.get("preprocessing_file") or prep_file
        except Exception:
            pass
    return model_file, prep_file


def _load_model(model_path: str):
    """Load model joblib/PyCaret dari path .pkl."""
    try:
        return joblib.load(model_path)
    except Exception as joblib_error:
        try:
            from pycaret.classification import load_model

            return load_model(os.path.splitext(model_path)[0], verbose=False)
        except Exception as pycaret_error:
            raise RuntimeError(
                "Model tidak dapat dimuat. Pastikan dependency PyCaret/scikit-learn "
                f"sesuai artifact notebook. joblib={joblib_error}; pycaret={pycaret_error}"
            ) from pycaret_error


def load_active(force: bool = False):
    """Muat (atau muat ulang) model & preprocessing aktif, dengan caching."""
    with _lock:
        _seed_default_artifacts_if_needed()
        model_file, prep_file = _resolve_active_files()
        if (
            not force
            and _cache["model"] is not None
            and _cache["model_file"] == model_file
            and _cache["prep_file"] == prep_file
        ):
            return _cache["model"], _cache["artifacts"], model_file

        model_path = os.path.join(settings.MODEL_DIR, model_file)
        prep_path = os.path.join(settings.PREP_DIR, prep_file)
        if not (os.path.exists(model_path) and os.path.exists(prep_path)):
            raise FileNotFoundError(
                f"Artifact aktif belum tersedia di Docker Volume "
                f"({model_path} / {prep_path}). Pastikan Data Scientist sudah build & deploy model."
            )
        model = _load_model(model_path)
        artifacts = joblib.load(prep_path)
        _cache.update({"model": model, "artifacts": artifacts, "model_file": model_file, "prep_file": prep_file})
        return model, artifacts, model_file


def create_features(df_in: pd.DataFrame) -> pd.DataFrame:
    """Feature extraction Step 7 notebook."""
    df = df_in.copy()
    bill_cols = [f"BILL_AMT{i}" for i in range(1, 7)]
    payamt_cols = [f"PAY_AMT{i}" for i in range(1, 7)]
    delay_cols = [f"PAY_{i}" for i in range(1, 7)]

    df["AVG_UTIL_RATIO"] = df[bill_cols].div(df["LIMIT_BAL"] + 1, axis=0).mean(axis=1)
    df["TOTAL_PAY_AMT"] = df[payamt_cols].sum(axis=1)
    df["AVG_PAY_AMT"] = df[payamt_cols].mean(axis=1)
    df["TOTAL_BILL_AMT"] = df[bill_cols].sum(axis=1)
    df["AVG_BILL_AMT"] = df[bill_cols].mean(axis=1)
    df["PAY_TO_BILL_RATIO"] = df["TOTAL_PAY_AMT"] / (df["TOTAL_BILL_AMT"] + 1)
    df["N_LATE_PAYMENTS"] = (df[delay_cols] > 0).sum(axis=1)
    df["MAX_DELAY"] = df[delay_cols].max(axis=1)
    df["BILL_TREND"] = df["BILL_AMT1"] - df["BILL_AMT6"]
    df["PAY_AMT_STD"] = df[payamt_cols].std(axis=1).fillna(0)
    return df


def preprocess_for_inference(df_raw: pd.DataFrame, artifacts: dict) -> pd.DataFrame:
    """Transformasi data mentah agar identik dengan preprocessing notebook."""
    df = df_raw.copy()

    if "PAY_0" in df.columns:
        df = df.rename(columns={"PAY_0": "PAY_1"})

    df["EDUCATION"] = df["EDUCATION"].apply(lambda x: np.nan if x in [0, 5, 6] else x)
    df["MARRIAGE"] = df["MARRIAGE"].apply(lambda x: np.nan if x == 0 else x)

    if all(k in artifacts for k in ("knn_feature_columns", "scaler_knn", "knn_imputer", "knn_valid_ranges")):
        knn_cols = artifacts["knn_feature_columns"]
        df_knn = df.reindex(columns=knn_cols)
        scaled = artifacts["scaler_knn"].transform(df_knn)
        imputed = artifacts["knn_imputer"].transform(scaled)
        inv = pd.DataFrame(
            artifacts["scaler_knn"].inverse_transform(imputed), columns=knn_cols, index=df.index
        )
        for col, (lo, hi) in artifacts["knn_valid_ranges"].items():
            df[col] = inv[col].round().clip(lo, hi)

    df["EDUCATION"] = df["EDUCATION"].fillna(artifacts["fallback_education"]).astype(int)
    df["MARRIAGE"] = df["MARRIAGE"].fillna(artifacts["fallback_marriage"]).astype(int)

    for col, (lower, upper) in artifacts["outlier_boundaries"].items():
        if col in df.columns:
            df[col] = np.clip(df[col], lower, upper)

    df = create_features(df)

    df = pd.get_dummies(df, columns=["MARRIAGE"])
    for col in artifacts["marriage_ohe_columns"]:
        if col not in df.columns:
            df[col] = 0

    df["SEX"] = df["SEX"].map(artifacts["sex_mapping"])
    if df["SEX"].isna().any():
        raise ValueError("Nilai SEX tidak valid. Gunakan kode 1 atau 2 sesuai dataset training.")
    df["SEX"] = df["SEX"].astype(int)

    missing = [c for c in artifacts["final_columns"] if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom hilang setelah preprocessing: {missing}")
    df = df[artifacts["final_columns"]]

    df[artifacts["columns_to_stdscaler"]] = artifacts["scaler"].transform(
        df[artifacts["columns_to_stdscaler"]]
    )
    return df


def _predict_label_score(model, X: pd.DataFrame) -> tuple[int, float]:
    """Prediksi label dan score memakai PyCaret, sama seperti app_fastapi1.py.

    PyCaret mengembalikan kolom `prediction_label` dan `prediction_score`.
    Fungsi ini sengaja tidak menghitung probability secara manual agar nilai
    `prediction_score` identik dengan output `predict_model()`.
    """
    pred = predict_model(model, data=X, verbose=False)

    required_columns = {"prediction_label", "prediction_score"}
    missing_columns = required_columns.difference(pred.columns)
    if missing_columns:
        raise ValueError(
            "Output PyCaret predict_model tidak memiliki kolom wajib: "
            f"{sorted(missing_columns)}. Kolom tersedia: {list(pred.columns)}"
        )

    label = int(pred["prediction_label"].values[0])
    score = float(pred["prediction_score"].values[0])
    return label, score


def predict_one(raw: dict) -> dict:
    """Prediksi satu peminjam. Return label, score, status."""
    model, artifacts, model_file = load_active()
    X = preprocess_for_inference(pd.DataFrame([raw]), artifacts)
    label, score = _predict_label_score(model, X)
    return {
        "prediction_label": int(label),
        "prediction_score": round(float(score), 4),
        "status": "Default" if int(label) == 1 else "Non-Default",
        "_model_file": model_file,
    }