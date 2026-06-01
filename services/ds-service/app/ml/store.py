"""Penyimpanan artifact & dataset: Docker Volume, DVC, dan pointer model aktif.

DVC remote = Google Drive (lihat .dvc/config). Pada container, fungsi di sini
menjalankan `dvc pull` untuk menarik dataset, lalu `dvc add` + push untuk
memversioning set data & artifact.
"""
import json
import os
import subprocess
from pathlib import Path

import joblib
import pandas as pd

from ..config import settings


def _ensure_dirs():
    for d in (settings.ARTIFACT_DIR, settings.MODEL_DIR, settings.PREP_DIR, settings.DATA_DIR):
        Path(d).mkdir(parents=True, exist_ok=True)


def _run(cmd: list[str], cwd: str | None = None) -> tuple[bool, str]:
    """Jalankan perintah shell; tidak meledak bila gagal (mis. tanpa kredensial DVC)."""
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
        ok = out.returncode == 0
        return ok, (out.stdout + out.stderr)
    except Exception as e:  # pragma: no cover
        return False, str(e)


# --------------------------- DATASET ---------------------------
def pull_dataset() -> pd.DataFrame:
    """Tarik dataset dari DVC (Google Drive) lalu muat sebagai DataFrame.

    Bila `dvc pull` gagal atau file belum ada, lempar FileNotFoundError agar
    router dapat memberi pesan yang jelas.
    """
    _ensure_dirs()
    dataset_path = os.path.join(settings.DATA_DIR, settings.DATASET_FILE)

    # 1) coba dvc pull (butuh .dvc/config + kredensial gdrive)
    _run(["dvc", "pull", "-q"], cwd=os.path.dirname(settings.DATA_DIR) or ".")

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"Dataset {settings.DATASET_FILE} belum tersedia di {settings.DATA_DIR}. "
            "Jalankan `dvc pull` atau letakkan file dataset pada volume data."
        )

    # baris pertama Excel berisi label X1..X23 → header=1
    if dataset_path.endswith((".xls", ".xlsx")):
        engine = "xlrd" if dataset_path.endswith(".xls") else "openpyxl"
        df = pd.read_excel(dataset_path, header=1, engine=engine)
    else:
        df = pd.read_csv(dataset_path)

    # seragamkan nama kolom X1..X23 → kanonik
    xmap = {
        "X1": "LIMIT_BAL", "X2": "SEX", "X3": "EDUCATION", "X4": "MARRIAGE", "X5": "AGE",
        "X6": "PAY_0", "X7": "PAY_2", "X8": "PAY_3", "X9": "PAY_4", "X10": "PAY_5", "X11": "PAY_6",
        "X12": "BILL_AMT1", "X13": "BILL_AMT2", "X14": "BILL_AMT3", "X15": "BILL_AMT4",
        "X16": "BILL_AMT5", "X17": "BILL_AMT6", "X18": "PAY_AMT1", "X19": "PAY_AMT2",
        "X20": "PAY_AMT3", "X21": "PAY_AMT4", "X22": "PAY_AMT5", "X23": "PAY_AMT6",
        "Y": "DEFAULT",
    }
    df = df.rename(columns={k: v for k, v in xmap.items() if k in df.columns})
    return df


def save_splits(Xtr, Xte, ytr, yte, run_id: str) -> list[dict]:
    """Simpan set train/test ke volume data (CSV) lalu track DVC."""
    _ensure_dirs()
    splits = {
        "X_train": Xtr, "X_test": Xte,
        "y_train": ytr.to_frame("DEFAULT"), "y_test": yte.to_frame("DEFAULT"),
    }
    meta = []
    for name, df in splits.items():
        fname = f"{name}_{run_id}.csv"
        path = os.path.join(settings.DATA_DIR, fname)
        df.to_csv(path, index=False)
        _run(["dvc", "add", path], cwd=os.path.dirname(settings.DATA_DIR) or ".")
        meta.append({"name": f"{name}.csv", "rows": int(len(df)), "dvc_path": path})
    _run(["dvc", "push", "-q"], cwd=os.path.dirname(settings.DATA_DIR) or ".")
    return meta


# --------------------------- ARTIFACT ---------------------------
def save_artifacts(preprocessing_artifacts: dict, model, version: str) -> dict:
    """Simpan .pkl preprocessing & model ke Docker Volume, lalu track DVC."""
    _ensure_dirs()
    v = version or "V1"
    prep_name = f"preprocessing_artifacts_{v}.pkl"
    model_name = f"best_credit_model_{v}.pkl"
    prep_path = os.path.join(settings.PREP_DIR, prep_name)
    model_path = os.path.join(settings.MODEL_DIR, model_name)

    joblib.dump(preprocessing_artifacts, prep_path)
    joblib.dump(model, model_path)

    for p in (prep_path, model_path):
        _run(["dvc", "add", p], cwd=os.path.dirname(settings.DATA_DIR) or ".")
    _run(["dvc", "push", "-q"], cwd=os.path.dirname(settings.DATA_DIR) or ".")

    def _size(p):
        try:
            kb = os.path.getsize(p) / 1024
            return f"{kb/1024:.1f} MB" if kb > 1024 else f"{kb:.0f} KB"
        except OSError:
            return None

    return {
        "preprocessing": prep_name, "model": model_name,
        "preprocessing_size": _size(prep_path), "model_size": _size(model_path),
        "preprocessing_path": prep_path, "model_path": model_path,
    }


# --------------------------- POINTER AKTIF ---------------------------
def set_active_pair(pair: dict):
    """Tulis pointer pasangan model aktif (dibaca ca-service untuk inference)."""
    _ensure_dirs()
    with open(settings.ACTIVE_POINTER, "w") as f:
        json.dump(pair, f)


def get_active_pair() -> dict | None:
    if os.path.exists(settings.ACTIVE_POINTER):
        with open(settings.ACTIVE_POINTER) as f:
            return json.load(f)
    return None


def list_pkl(folder: str) -> list[str]:
    p = Path(folder)
    return sorted([f.name for f in p.glob("*.pkl")]) if p.exists() else []


# --------------------------- EVALUASI (cache) ---------------------------
def save_evaluation(version: str, evaluation: dict):
    """Simpan hasil evaluasi (learning curve, CM, report) agar dapat dibuka lagi."""
    _ensure_dirs()
    path = os.path.join(settings.ARTIFACT_DIR, f"eval_{version}.json")
    with open(path, "w") as f:
        json.dump(evaluation, f)


def load_evaluation(version: str) -> dict | None:
    path = os.path.join(settings.ARTIFACT_DIR, f"eval_{version}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None
