"""Konfigurasi terpusat Data Scientist Sistem (dibaca dari environment variables)."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ---- Identitas service ----
    SERVICE_NAME: str = "RiskFinder · Data Scientist Sistem"
    API_PREFIX: str = ""

    # ---- JWT ----
    # WAJIB diganti di produksi (lihat .env). Dipakai bersama antar service agar token kompatibel.
    JWT_SECRET: str = "ganti-dengan-secret-acak-panjang-di-produksi"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 jam

    # ---- PostgreSQL ----
    DATABASE_URL: str = "postgresql+psycopg2://riskfinder:riskfinder@postgres:5432/riskfinder"

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
        "https://docs.google.com/spreadsheets/d/1M5IpMEQ1KVq0WT_nt-iEJ0l6-7OEG84O/edit"
    )

    # ---- MLflow ----
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"
    MLFLOW_EXPERIMENT: str = "credit-risk-build"

    # ---- CORS (origin frontend Vercel) ----
    CORS_ORIGINS: str = "http://localhost:5173,https://*.vercel.app"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
