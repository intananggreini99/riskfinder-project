# ===== RiskFinder · Credit Analysis Sistem (Container 2) =====
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# Artifact notebook dibake ke dua lokasi:
# - /artifacts      : langsung tersedia pada deployment tanpa volume (Railway/Render)
# - /seed-artifacts : sumber seed saat Docker Volume lokal menimpa /artifacts
COPY artifacts /artifacts
COPY artifacts /seed-artifacts

RUN mkdir -p /artifacts/models /artifacts/preprocessing

EXPOSE 8082

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8082/health || exit 1

CMD ["sh", "-c", "mkdir -p /artifacts/models /artifacts/preprocessing && cp -rn /seed-artifacts/. /artifacts/ 2>/dev/null || true; uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8082}"]