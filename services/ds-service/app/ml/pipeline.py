"""Orkestrasi Build Model (dipakai bersama oleh API dan MLflow Project).

Modul ini menjadi *satu sumber kebenaran* untuk menjalankan keseluruhan
preprocessing + modeling (Step 1–17 pada Preprocessing_Modeling_EndToEnd.ipynb),
mencatat ke MLflow, menyimpan artifact .pkl ke Docker Volume + DVC, menulis set
data ke DVC + PostgreSQL, lalu meregistrasi katalog model/preprocessing.

Dipanggil dari dua tempat:
  1. Router FastAPI  (app/routers/mlflow_service.py)
  2. Entry point MLflow Project (mlproject/train_pipeline.py) — dijalankan oleh
     perintah `mlflow run` ketika Data Scientist menekan tombol Run pada web UI.
"""
from __future__ import annotations

import os
import re
import uuid

from ..config import settings
from . import store
from .preprocessing import run_preprocessing
from .training import train_and_evaluate


def _noop(*_args, **_kwargs):
    pass


def normalize_version(raw: str | None) -> str:
    """Ubah input bebas (mis. 'model_V2', ' v3 ', '') menjadi token versi rapi 'V2'."""
    if not raw:
        return "V1"
    v = str(raw).strip()
    # buang prefiks umum yang tidak perlu masuk ke nama file
    v = re.sub(r"^(model[_-]?|preprocessing[_-]?|best[_-]?credit[_-]?model[_-]?)", "", v, flags=re.I)
    v = v.strip().replace(" ", "_")
    if not v:
        return "V1"
    # bila murni angka → beri awalan V (V2), selain itu pertahankan apa adanya (V2, exp1, dst.)
    if re.fullmatch(r"\d+", v):
        return f"V{v}"
    if re.fullmatch(r"[vV]\d+", v):
        return f"V{v[1:]}"
    return v


def _next_auto_version() -> str:
    """Tentukan versi berikutnya (V1, V2, ...) berdasar artifact model yang sudah ada di Volume."""
    existing = store.list_pkl(settings.MODEL_DIR)
    nums = []
    for name in existing:
        m = re.search(r"_V(\d+)\.pkl$", name)
        if m:
            nums.append(int(m.group(1)))
    return f"V{(max(nums) + 1) if nums else 1}"


def run_build(cfg: dict, db=None, log=None) -> dict:
    """Jalankan pipeline Build Model end-to-end.

    Parameters
    ----------
    cfg : dict  → {test_size, random_state, n_trials, model_version, auto_version?}
    db  : Session | None  → bila diberikan, katalog ditulis ke PostgreSQL (skema ds)
    log : callable | None  → callback untuk menyiarkan log proses (mis. print / list.append)

    Returns
    -------
    dict siap dipakai sebagai RunResult + metadata tambahan (mlflow_run_id, version).
    """
    log = log or _noop
    test_size = float(cfg.get("test_size", 0.30))
    random_state = int(cfg.get("random_state", 42))
    n_trials = int(cfg.get("n_trials", 80))

    # Versi artifact: pakai label user bila ada, kalau kosong → auto-increment V1/V2/...
    if cfg.get("model_version"):
        version = normalize_version(cfg.get("model_version"))
    elif cfg.get("auto_version", True):
        version = _next_auto_version()
    else:
        version = "V1"

    run_id = "run_" + uuid.uuid4().hex[:10]

    log(f"[MLflow Project] entry point=main  run_id={run_id}  version={version}")
    log(f"[params] test_size={test_size} random_state={random_state} n_trials={n_trials}")

    # 1) Dataset dari DVC (Google Drive) → DataFrame
    log("[1/7] dvc pull → memuat dataset defaultCreditCardClients.xls ...")
    df = store.pull_dataset()
    log(f"      dataset OK · {len(df):,} baris × {df.shape[1]} kolom")

    # 2) MLflow tracking (opsional; tidak menggagalkan run bila server mati)
    mlflow_run_id = None
    mlflow = None
    try:
        import mlflow as _mlflow
        _mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        _mlflow.set_experiment(settings.MLFLOW_EXPERIMENT)
        # bila sudah ada active run (mis. dipanggil di dalam `mlflow run`), pakai itu
        active = _mlflow.active_run()
        if active is None:
            active = _mlflow.start_run(run_name=run_id)
        mlflow = _mlflow
        mlflow_run_id = active.info.run_id
        mlflow.log_params({
            "entry_point": "main", "test_size": test_size,
            "random_state": random_state, "n_trials": n_trials, "version": version,
        })
        log(f"[mlflow] tracking aktif · run={mlflow_run_id} · experiment={settings.MLFLOW_EXPERIMENT}")
    except Exception as e:  # pragma: no cover
        log(f"[mlflow] tracking dilewati ({e}); pipeline tetap berjalan")

    # 3) Preprocessing (Step 1–11)
    log("[2/7] preprocessing (Step 1–11) ...")
    Xtr, Xte, ytr, yte, artifacts = run_preprocessing(df, test_size, random_state)
    log(f"      fitur final = {len(artifacts['final_columns'])} · train={len(Xtr):,} test={len(Xte):,}")

    # 4) Modeling (Step 12–16)
    log("[3/7] modeling: compare → tuning → validation → evaluasi (Step 12–16) ...")
    best_model, metrics, evaluation = train_and_evaluate(Xtr, Xte, ytr, yte, n_trials)
    log(f"      algoritma terbaik = {metrics['algorithm']}")
    log(f"      ROC AUC train={metrics['roc_auc_train']} test={metrics['roc_auc_test']} gap={metrics['gap']}")

    # 5) Simpan artifact (Step 17) → Docker Volume + DVC + cache evaluasi
    log("[4/7] menyimpan artifact .pkl → Docker Volume + DVC (Step 17) ...")
    art = store.save_artifacts(artifacts, best_model, version)
    store.save_evaluation(version, {**evaluation, "pair_name": f"Model_{version} + preprocessing_{version}"})
    log(f"      {art['preprocessing']} ({art['preprocessing_size']}) · {art['model']} ({art['model_size']})")

    # 6) Simpan set data → DVC (CSV) + metadata PostgreSQL
    log("[5/7] menulis set train/test → DVC (CSV) ...")
    splits = store.save_splits(Xtr, Xte, ytr, yte, run_id)

    # 7) Log metrik ke MLflow & tutup run (hanya bila run kita yang membuka)
    if mlflow:
        try:
            mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
            mlflow.log_artifact(art["preprocessing_path"]) if os.path.exists(art["preprocessing_path"]) else None
            mlflow.log_artifact(art["model_path"]) if os.path.exists(art["model_path"]) else None
        except Exception:
            pass

    # 8) Persist katalog ke PostgreSQL (bila ada session)
    if db is not None:
        log("[6/7] meregistrasi katalog model & preprocessing → PostgreSQL ...")
        _persist_catalog(db, run_id, mlflow_run_id, test_size, random_state, n_trials,
                         version, artifacts, art, metrics, splits, log)

    log("[7/7] selesai. Artifact siap dipasangkan di halaman Monitoring Model.")

    return {
        "run_id": run_id,
        "mlflow_run_id": mlflow_run_id,
        "version": version,
        "algorithm": metrics["algorithm"],
        "metrics": {
            "roc_auc_test": f"{metrics['roc_auc_test']:.4f}",
            "roc_auc_train": f"{metrics['roc_auc_train']:.4f}",
            "f1": f"{metrics['f1']:.4f}",
            "recall": f"{metrics['recall']:.4f}",
            "gap": f"{metrics['gap']:.4f}",
        },
        "artifacts": {
            "preprocessing": art["preprocessing"], "model": art["model"],
            "preprocessing_size": art["preprocessing_size"], "model_size": art["model_size"],
        },
        "datasets": [{"name": s["name"], "rows": s["rows"]} for s in splits],
    }


def _persist_catalog(db, run_id, mlflow_run_id, test_size, random_state, n_trials,
                     version, artifacts, art, metrics, splits, log=_noop):
    """Tulis baris katalog (run, model, preprocessing, split) ke skema ds. Aman bila gagal."""
    from .. import models
    try:
        db.add(models.TrainingRun(
            run_id=run_id, mlflow_run_id=mlflow_run_id,
            test_size=test_size, random_state=random_state, n_trials=n_trials,
            algorithm=metrics["algorithm"],
            roc_auc_train=metrics["roc_auc_train"], roc_auc_test=metrics["roc_auc_test"],
            gap_train_test=metrics["gap"], f1_score=metrics["f1"],
            precision_score=metrics["precision"], recall_score=metrics["recall"],
            accuracy_score=metrics["accuracy"],
        ))
        db.add(models.PreprocessingArtifact(
            preprocessing_id=f"preprocessing_{version}", filename=art["preprocessing"],
            run_id=run_id, n_features=len(artifacts["final_columns"]),
        ))
        db.add(models.ModelArtifact(
            model_id=f"model_{version}", filename=art["model"], run_id=run_id,
            algorithm=metrics["algorithm"], roc_auc=metrics["roc_auc_test"],
        ))
        for s in splits:
            db.add(models.DatasetSplit(
                run_id=run_id, split_name=s["name"].replace(".csv", ""),
                filename=s["name"], n_rows=s["rows"], dvc_path=s.get("dvc_path"),
            ))
        db.commit()
        log(f"      katalog tersimpan: model_{version}, preprocessing_{version}")
    except Exception as e:  # katalog gagal tidak boleh menggagalkan pipeline
        db.rollback()
        log(f"      [peringatan] gagal menulis katalog PostgreSQL: {e}")
