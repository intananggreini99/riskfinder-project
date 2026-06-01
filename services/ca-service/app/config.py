"""Konfigurasi terpusat Credit Analysis Sistem."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    SERVICE_NAME: str = "RiskFinder · Credit Analysis Sistem"

    # ---- JWT (secret SAMA dengan ds-service agar token kompatibel) ----
    JWT_SECRET: str = "ganti-dengan-secret-acak-panjang-di-produksi"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8

    # ---- PostgreSQL (database sama) ----
    DATABASE_URL: str = "postgresql+psycopg2://riskfinder:riskfinder@postgres:5432/riskfinder"

    # ---- Docker Volume (artifact .pkl dari Data Scientist) ----
    ARTIFACT_DIR: str = "/artifacts"
    MODEL_DIR: str = "/artifacts/models"
    PREP_DIR: str = "/artifacts/preprocessing"
    ACTIVE_POINTER: str = "/artifacts/active_pair.json"

    # Fallback bila tidak ada pointer aktif (mis. model_final.pkl)
    DEFAULT_MODEL_FILE: str = "best_credit_model_V1.pkl"
    DEFAULT_PREP_FILE: str = "preprocessing_artifacts_V1.pkl"

    CORS_ORIGINS: str = "http://localhost:5173,https://*.vercel.app"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
