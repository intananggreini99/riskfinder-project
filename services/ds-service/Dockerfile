# ===== RiskFinder · Data Scientist Sistem (Container 1) =====
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgomp1 git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY mlproject ./mlproject
COPY data ./data
# Artifact notebook bawaan untuk katalog/deploy awal.
COPY artifacts /artifacts
COPY artifacts /seed-artifacts

RUN mkdir -p /artifacts/models /artifacts/preprocessing /data

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8081/health || exit 1

CMD ["sh", "-c", "mkdir -p /artifacts/models /artifacts/preprocessing && cp -rn /seed-artifacts/. /artifacts/ 2>/dev/null || true; uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8081}"]
