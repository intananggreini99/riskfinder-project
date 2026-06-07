"""Entry point MLflow Project — Build Model RiskFinder.

Dijalankan oleh `mlflow run` (atau `python train_pipeline.py ...`). Mereplikasi
keseluruhan alur Preprocessing_Modeling_EndToEnd.ipynb (Step 1–17):
  load dataset (DVC) → preprocessing → modeling → evaluasi
  → simpan preprocessing_artifacts_Vx.pkl & best_credit_model_Vx.pkl
  → tulis set train/test ke DVC → registrasi katalog ke PostgreSQL.

Hasil ringkas ditulis ke file JSON agar backend (FastAPI) dapat membacanya dan
menampilkannya di halaman Service ML Flow.
"""
import argparse
import json
import os
import sys
import traceback

# Pastikan package aplikasi (app.*) dapat di-import saat dijalankan oleh `mlflow run`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # → /app

from app.ml import pipeline  # noqa: E402
from app.config import settings  # noqa: E402

RESULT_PATH = os.environ.get("RF_RUN_RESULT", os.path.join(settings.ARTIFACT_DIR, "last_run_result.json"))


def _make_db():
    """Sesi PostgreSQL sendiri (proses ini terpisah dari proses FastAPI)."""
    try:
        from app.database import SessionLocal
        return SessionLocal()
    except Exception as e:
        print(f"[db] tidak dapat membuka sesi PostgreSQL ({e}); katalog dilewati")
        return None


def main():
    ap = argparse.ArgumentParser(description="RiskFinder MLflow Project — Build Model")
    ap.add_argument("--test_size", type=float, default=0.30)
    ap.add_argument("--random_state", type=float, default=42)
    ap.add_argument("--n_trials", type=float, default=80)
    ap.add_argument("--model_version", type=str, default="")
    ap.add_argument("--only", type=str, default="", help="kosong=main; 'preprocessing'=hanya preprocessing")
    args = ap.parse_args()

    cfg = {
        "test_size": float(args.test_size),
        "random_state": int(args.random_state),
        "n_trials": int(args.n_trials),
        "model_version": (args.model_version or "").strip(),
    }

    db = _make_db()
    try:
        print("=" * 64)
        print(" RiskFinder · MLflow Project — Build Model")
        print("=" * 64)
        result = pipeline.run_build(cfg, db=db, log=print)
        result["status"] = "success"
    except FileNotFoundError as e:
        result = {"status": "error", "error": str(e),
                  "hint": "Dataset belum tersedia. Jalankan `dvc pull` atau sediakan dataset pada volume /data."}
        print("[ERROR]", e)
    except Exception as e:  # noqa: BLE001
        result = {"status": "error", "error": str(e), "trace": traceback.format_exc()}
        print("[ERROR]", e)
        traceback.print_exc()
    finally:
        if db is not None:
            db.close()

    # Tulis hasil agar dapat dibaca backend
    try:
        os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
        with open(RESULT_PATH, "w") as f:
            json.dump(result, f)
        print(f"[result] ditulis ke {RESULT_PATH}")
    except Exception as e:
        print(f"[result] gagal menulis hasil: {e}")

    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
