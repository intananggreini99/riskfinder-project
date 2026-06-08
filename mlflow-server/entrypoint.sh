#!/usr/bin/env sh
# mlflow-server/entrypoint.sh
# ---------------------------------------------------------------------------
# Menjalankan MLflow Tracking Server di Railway (Bab 5.3 & 5.9 panduan).
# Perintahnya identik dengan yang ada di panduan, ditambah dua pengaman:
#   1) Default PORT=5000 bila variabel belum diset (mis. saat run lokal /
#      saat service MLflow di-private tanpa domain — lihat INTEGRATION).
#   2) Normalisasi skema DB  postgres://  ->  postgresql://
#      SQLAlchemy modern menolak "postgres://" (Gotcha penting Bab 5.6).
# ---------------------------------------------------------------------------
set -e

# --- 1) PORT: pakai nilai dari Railway, atau 5000 sebagai default aman ---
: "${PORT:=5000}"

# --- 2) Perbaiki skema backend store bila masih postgres:// ---
if [ -n "${MLFLOW_BACKEND_STORE_URI}" ]; then
  case "${MLFLOW_BACKEND_STORE_URI}" in
    postgres://*)
      MLFLOW_BACKEND_STORE_URI="postgresql://${MLFLOW_BACKEND_STORE_URI#postgres://}"
      echo "[entrypoint] Skema DB dinormalisasi: postgres:// -> postgresql://"
      ;;
  esac
fi
export MLFLOW_BACKEND_STORE_URI

# --- Log diagnostik (kredensial sengaja tidak dicetak) ---
echo "[entrypoint] MLflow listen di  : 0.0.0.0:${PORT}"
echo "[entrypoint] Backend store     : ${MLFLOW_BACKEND_STORE_URI%%:*}://… (disembunyikan)"
echo "[entrypoint] Artifacts dest     : ${MLFLOW_ARTIFACTS_DESTINATION:-(belum diset)}"
echo "[entrypoint] S3 endpoint        : ${MLFLOW_S3_ENDPOINT_URL:-(default AWS)}"

# Server WAJIB bind ke 0.0.0.0 dan ke $PORT, dan memakai --serve-artifacts
# agar klien (kode training / ds-service) tak perlu kredensial S3 (Bab 1 & 5.9).
exec mlflow server \
  --backend-store-uri "${MLFLOW_BACKEND_STORE_URI}" \
  --artifacts-destination "${MLFLOW_ARTIFACTS_DESTINATION}" \
  --serve-artifacts \
  --host 0.0.0.0 \
  --port "${PORT}"
