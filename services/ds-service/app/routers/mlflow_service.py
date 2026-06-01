"""Router Service ML Flow (Build Model) — Divisi Data Scientist.

Menjalankan preprocessing + modeling end-to-end, mencatat ke MLflow,
menyimpan artifact ke Docker Volume + DVC, dan set data ke DVC + PostgreSQL.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..security import get_current_user
from ..schemas import RunConfig, RunResult, ArtifactInfo, DatasetInfo
from ..ml import store
from ..ml.preprocessing import run_preprocessing
from ..ml.training import train_and_evaluate
from .. import models

router = APIRouter(prefix="/mlflow", tags=["ml-flow"])


@router.post("/pull-data")
def pull_data(user=Depends(get_current_user)):
    """1.a.1 — tarik dataset dari DVC (Google Drive)."""
    try:
        df = store.pull_dataset()
        return {"status": "ok", "rows": int(len(df)), "columns": int(df.shape[1]),
                "source": settings.GDRIVE_DATASET_URL, "file": settings.DATASET_FILE}
    except FileNotFoundError as e:
        raise HTTPException(status_code=424, detail=str(e))


@router.post("/run", response_model=RunResult)
def run_pipeline(cfg: RunConfig, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """1.a.2–1.a.4 — preprocessing + modeling + simpan artifact & set data."""
    # 1) muat dataset
    try:
        df = store.pull_dataset()
    except FileNotFoundError as e:
        raise HTTPException(status_code=424, detail=str(e))

    run_id = "run_" + uuid.uuid4().hex[:10]
    version = cfg.model_version or "V1"

    # 2) MLflow tracking (opsional, tidak menggagalkan run bila server mati)
    mlflow_run_id = None
    try:
        import mlflow
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment(settings.MLFLOW_EXPERIMENT)
        mlflow.start_run(run_name=run_id)
        mlflow_run_id = mlflow.active_run().info.run_id
        mlflow.log_params({"test_size": cfg.test_size, "random_state": cfg.random_state, "n_trials": cfg.n_trials})
    except Exception:
        mlflow = None

    # 3) preprocessing (Step 1–11)
    Xtr, Xte, ytr, yte, artifacts = run_preprocessing(df, cfg.test_size, cfg.random_state)

    # 4) modeling (Step 12–16)
    best_model, metrics, evaluation = train_and_evaluate(Xtr, Xte, ytr, yte, cfg.n_trials)

    # 5) simpan artifact (Step 17) → Docker Volume + DVC + cache evaluasi
    art = store.save_artifacts(artifacts, best_model, version)
    store.save_evaluation(version, {**evaluation, "pair_name": f"Model_{version} + preprocessing_{version}"})

    # 6) simpan set data → DVC (CSV) + metadata PostgreSQL
    splits = store.save_splits(Xtr, Xte, ytr, yte, run_id)

    if mlflow:
        try:
            mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
            mlflow.end_run()
        except Exception:
            pass

    # 7) persist katalog ke PostgreSQL
    try:
        run = models.TrainingRun(
            run_id=run_id, mlflow_run_id=mlflow_run_id,
            test_size=cfg.test_size, random_state=cfg.random_state, n_trials=cfg.n_trials,
            algorithm=metrics["algorithm"],
            roc_auc_train=metrics["roc_auc_train"], roc_auc_test=metrics["roc_auc_test"],
            gap_train_test=metrics["gap"], f1_score=metrics["f1"],
            precision_score=metrics["precision"], recall_score=metrics["recall"],
            accuracy_score=metrics["accuracy"],
        )
        db.add(run)
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
    except Exception:
        db.rollback()  # katalog gagal tidak menggagalkan respons pipeline

    return RunResult(
        run_id=run_id,
        metrics={
            "roc_auc_test": f"{metrics['roc_auc_test']:.4f}",
            "roc_auc_train": f"{metrics['roc_auc_train']:.4f}",
            "f1": f"{metrics['f1']:.4f}",
            "recall": f"{metrics['recall']:.4f}",
            "gap": f"{metrics['gap']:.4f}",
        },
        artifacts=ArtifactInfo(
            preprocessing=art["preprocessing"], model=art["model"],
            preprocessing_size=art["preprocessing_size"], model_size=art["model_size"],
        ),
        datasets=[DatasetInfo(name=s["name"], rows=s["rows"]) for s in splits],
    )
