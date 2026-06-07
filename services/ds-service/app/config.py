"""Konfigurasi terpusat Data Scientist Sistem (dibaca dari environment variables)."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ---- Identitas service ----
    SERVICE_NAME: str = "RiskFinder · Data Scientist Sistem"
    API_PREFIX: str = ""

    # ---- JWT ----
    # WAJIB diganti di produksi (lihat .env). Dipakai bersama antar service agar token kompatibel.
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 jam

    # ---- PostgreSQL ----
    DATABASE_URL: str = ""

    # ---- Docker Volume (penyimpanan artifact .pkl) ----
    ARTIFACT_DIR: str = "/artifacts"          # mount Docker Volume bersama
    MODEL_DIR: str = "/artifacts/models"
    PREP_DIR: str = "/artifacts/preprocessing"
    ACTIVE_POINTER: str = "/artifacts/active_pair.json"  # menunjuk pasangan model aktif

    # ---- DVC / dataset ----
    DATA_DIR: str = "/data"
    DATASET_FILE: str = "defaultCreditCardClients.xls"
    # URL Google Drive sumber dataset (di-track DVC sebagai remote gdrive)
    GDRIVE_DATASET_URL: str = (
        "https://drive.google.com/drive/folders/1qhTv9KOVAn08gl8OQcAbsRoJ9wPJ8I2d?usp=sharing"
    )

    # ---- MLflow ----
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"     # dipakai service untuk logging
    MLFLOW_EXPERIMENT: str = "credit-risk-build"
    # URL web UI MLflow yang dapat dibuka BROWSER (untuk iframe & tombol "Buka MLflow").
    # Lokal: http://localhost:5000 · Produksi: URL publik server MLflow Anda.
    MLFLOW_UI_URL: str = "http://localhost:5000"
    # Lokasi MLflow Project di dalam container (berisi MLproject + train_pipeline.py)
    MLPROJECT_DIR: str = "/app/mlproject"

    # ---- CORS (origin frontend Vercel) ----
    CORS_ORIGINS: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
