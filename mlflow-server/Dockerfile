# mlflow-server/Dockerfile
# ===========================================================================
# MLflow Tracking Server siap-produksi untuk Railway — Metode B (Bab 5.3).
# ===========================================================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# curl dipakai untuk HEALTHCHECK & diagnostik. Wheel psycopg2-binary/boto3
# tidak butuh toolchain kompilasi, jadi dependensi sistem cukup minimal.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Install dependensi Python lebih dulu agar layer ini ter-cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skrip start (menangani $PORT default + perbaikan skema postgres://).
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Railway menyuntikkan $PORT secara otomatis saat runtime; EXPOSE hanya
# bersifat dokumentatif.
EXPOSE 5000

# Healthcheck opsional — Railway juga punya healthcheck sendiri (Bab 5.6).
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT:-5000}/health" || exit 1

# Server WAJIB bind ke 0.0.0.0 dan ke $PORT (lihat catatan $PORT Bab 5.3).
# Bind ke 127.0.0.1 atau port tetap menyebabkan error 502 di Railway.
ENTRYPOINT ["/app/entrypoint.sh"]

# --- Alternatif tanpa entrypoint (persis seperti contoh CMD di Bab 5.3) ---
# Hapus dua baris ENTRYPOINT/HEALTHCHECK di atas bila ingin memakai ini.
# CMD mlflow server \
#     --backend-store-uri "${MLFLOW_BACKEND_STORE_URI}" \
#     --artifacts-destination "${MLFLOW_ARTIFACTS_DESTINATION}" \
#     --serve-artifacts \
#     --host 0.0.0.0 \
#     --port ${PORT}
