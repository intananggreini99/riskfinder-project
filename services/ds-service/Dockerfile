# ===== RiskFinder · Data Scientist Sistem (Container 1) =====
FROM python:3.11-slim

# Dependensi sistem untuk psycopg2, xgboost (libgomp), dan git (DVC)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgomp1 git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependensi Python lebih dulu (memanfaatkan cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin kode aplikasi
COPY app ./app
COPY mlproject ./mlproject
COPY artifacts /artifacts
# Dataset di-bake agar Build Model (MLflow Project) tetap jalan walau DVC remote
# (Google Drive) tidak terjangkau dari host container. Bila kredensial DVC tersedia,
# store.pull_dataset() akan menyegarkannya via `dvc pull` lebih dulu.
COPY data /data

# Direktori artifact (Docker Volume) & data (DVC)
RUN mkdir -p /artifacts/models /artifacts/preprocessing /data

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8081/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8081}"]
