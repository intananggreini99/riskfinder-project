"""Router Service ML Flow (Build Model) — Divisi Data Scientist.

Memberi web UI MLflow Projects: menyajikan source code project (preprocessing +
modeling = Step 1–17), menjalankan `mlflow run` saat Data Scientist menekan Run,
mencatat ke MLflow, lalu menyimpan preprocessing_artifacts_Vx.pkl &
best_credit_model_Vx.pkl secara otomatis ke Docker Volume + DVC + PostgreSQL.
"""
import json
import os
import subprocess
import sys

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..security import get_current_user
from ..schemas import (
    RunConfig, RunResult, ArtifactInfo, DatasetInfo,
    ProjectFile, ProjectSpec, ProjectRunRequest, ProjectRunResult,
)
from ..ml import store, pipeline

router = APIRouter(prefix="/mlflow", tags=["ml-flow"])

# Berkas project yang ditampilkan di web UI (path relatif → metadata tampilan)
_PROJECT_FILES = [
    ("mlproject/MLproject",       "MLproject",        "yaml",   False),
    ("mlproject/python_env.yaml", "python_env.yaml",  "yaml",   False),
    ("mlproject/train_pipeline.py", "train_pipeline.py", "python", True),
    ("app/ml/preprocessing.py",   "preprocessing.py", "python", True),
    ("app/ml/training.py",        "training.py",      "python", True),
]
_APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # → /app


def _read(path: str) -> str:
    full = os.path.join(_APP_ROOT, path)
    try:
        with open(full, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:  # pragma: no cover
        return f"# (tidak dapat memuat {path}: {e})"


# --------------------------- META ---------------------------
@router.get("/ui-url")
def mlflow_ui(user=Depends(get_current_user)):
    """URL web UI MLflow yang dapat dibuka browser (iframe / tab baru)."""
    return {"url": settings.MLFLOW_UI_URL, "experiment": settings.MLFLOW_EXPERIMENT}


@router.get("/projects/spec", response_model=ProjectSpec)
def project_spec(user=Depends(get_current_user)):
    """Spesifikasi MLflow Project: source code + parameter default untuk web UI."""
    files = [
        ProjectFile(path=p, label=label, language=lang, editable=ed, content=_read(p))
        for (p, label, lang, ed) in _PROJECT_FILES
    ]
    return ProjectSpec(
        name="riskfinder-credit-risk",
        entry_points=["main", "preprocessing"],
        default_params={"test_size": 0.30, "random_state": 42, "n_trials": 80, "model_version": ""},
        files=files,
        mlflow_ui_url=settings.MLFLOW_UI_URL,
        experiment=settings.MLFLOW_EXPERIMENT,
        dataset_file=settings.DATASET_FILE,
        next_version=pipeline._next_auto_version(),
    )


# --------------------------- DATA ---------------------------
@router.post("/pull-data")
def pull_data(user=Depends(get_current_user)):
    """1.a.1 — tarik dataset dari DVC (Google Drive)."""
    try:
        df = store.pull_dataset()
        return {"status": "ok", "rows": int(len(df)), "columns": int(df.shape[1]),
                "source": settings.GDRIVE_DATASET_URL, "file": settings.DATASET_FILE}
    except FileNotFoundError as e:
        raise HTTPException(status_code=424, detail=str(e))


# --------------------------- RUN (via MLflow Projects) ---------------------------
@router.post("/projects/run", response_model=ProjectRunResult)
def run_project(body: ProjectRunRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Jalankan MLflow Project (`mlflow run`) lalu kembalikan log + ringkasan hasil.

    Entry point `main` menjalankan Step 1–17 dan menyimpan artifact .pkl otomatis.
    """
    entry = body.entry_point if body.entry_point in ("main", "preprocessing") else "main"
    version_arg = (body.model_version or "").strip()
    result_path = os.path.join(settings.ARTIFACT_DIR, "last_run_result.json")

    # bersihkan hasil lama agar tidak salah baca
    try:
        os.remove(result_path)
    except OSError:
        pass

    env = {
        **os.environ,
        "PYTHONPATH": _APP_ROOT,
        "RF_RUN_RESULT": result_path,
        "MLFLOW_TRACKING_URI": settings.MLFLOW_TRACKING_URI,
    }
    params = [
        "-P", f"test_size={body.test_size}",
        "-P", f"random_state={body.random_state}",
        "-P", f"n_trials={body.n_trials}",
        "-P", f"model_version={version_arg}",
    ]
    mlflow_cmd = ["mlflow", "run", settings.MLPROJECT_DIR, "-e", entry, "--env-manager", "local", *params]
    cmd_str = (
        f"mlflow run {settings.MLPROJECT_DIR} -e {entry} --env-manager local "
        f"-P test_size={body.test_size} -P random_state={body.random_state} "
        f"-P n_trials={body.n_trials} -P model_version=\"{version_arg}\""
    )

    logs = f"$ {cmd_str}\n"
    ran = False
    try:
        proc = subprocess.run(mlflow_cmd, cwd=settings.MLPROJECT_DIR, env=env,
                              capture_output=True, text=True, timeout=1800)
        logs += (proc.stdout or "") + (proc.stderr or "")
        ran = True
    except FileNotFoundError:
        logs += "[info] CLI `mlflow` tidak ditemukan; menjalankan entry point langsung.\n"
    except subprocess.TimeoutExpired:
        logs += "\n[ERROR] eksekusi melebihi batas waktu (30 menit).\n"

    # Fallback: bila `mlflow run` tak menulis hasil (gagal start), eksekusi script langsung.
    if not os.path.exists(result_path):
        if ran:
            logs += "\n[info] `mlflow run` tidak menghasilkan output; fallback eksekusi langsung.\n"
        fb = [sys.executable or "python", "train_pipeline.py",
              "--test_size", str(body.test_size), "--random_state", str(body.random_state),
              "--n_trials", str(body.n_trials), "--model_version", version_arg]
        if entry == "preprocessing":
            fb += ["--only", "preprocessing"]
        logs += f"$ python train_pipeline.py (entry={entry})\n"
        try:
            proc = subprocess.run(fb, cwd=settings.MLPROJECT_DIR, env=env,
                                  capture_output=True, text=True, timeout=1800)
            logs += (proc.stdout or "") + (proc.stderr or "")
        except Exception as e:  # noqa: BLE001
            logs += f"\n[ERROR] fallback gagal: {e}\n"

    # Baca ringkasan hasil yang ditulis entry point
    data = {}
    if os.path.exists(result_path):
        try:
            with open(result_path) as f:
                data = json.load(f)
        except Exception as e:  # pragma: no cover
            logs += f"\n[ERROR] gagal membaca hasil: {e}\n"

    status = data.get("status", "error")
    art = data.get("artifacts")
    return ProjectRunResult(
        status=status,
        command=cmd_str,
        logs=logs.strip(),
        run_id=data.get("run_id"),
        mlflow_run_id=data.get("mlflow_run_id"),
        version=data.get("version"),
        algorithm=data.get("algorithm"),
        metrics=data.get("metrics"),
        artifacts=ArtifactInfo(**art) if art else None,
        datasets=[DatasetInfo(**d) for d in data.get("datasets", [])],
        mlflow_ui_url=settings.MLFLOW_UI_URL,
        error=data.get("error"),
    )


# --------------------------- RUN (legacy, sinkron in-process) ---------------------------
@router.post("/run", response_model=RunResult)
def run_pipeline(cfg: RunConfig, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Kompatibilitas: jalankan pipeline langsung di proses API (tanpa subprocess)."""
    try:
        res = pipeline.run_build(cfg.model_dump(), db=db, log=lambda *_: None)
    except FileNotFoundError as e:
        raise HTTPException(status_code=424, detail=str(e))
    return RunResult(
        run_id=res["run_id"], metrics=res["metrics"],
        artifacts=ArtifactInfo(**res["artifacts"]),
        datasets=[DatasetInfo(**d) for d in res["datasets"]],
    )
