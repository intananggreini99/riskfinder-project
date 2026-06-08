# mlflow-server — MLflow Tracking Server untuk Railway (Metode B)

Source code untuk **"Metode B — Deploy Manual dari Dockerfile"** dari
*Panduan-Deploy-MLflow-ke-Railway.docx*. Dipakai bersama proyek **RiskFinder**.

Server ini berjalan dengan mode `--serve-artifacts`, sehingga klien (kode
training / `ds-service`) **tidak butuh kredensial S3** — cukup tracking URI +
Basic Auth.

## Isi direktori

| Berkas | Untuk service | Fungsi |
| --- | --- | --- |
| `Dockerfile` | **MLflow** | Build image MLflow Tracking Server (Bab 5.3). |
| `requirements.txt` | **MLflow** | `mlflow`, `psycopg2-binary`, `boto3` (Bab 5.2). |
| `entrypoint.sh` | **MLflow** | Start command + default `$PORT` + perbaikan skema `postgres://` (Bab 5.6). |
| `Caddyfile` | **Caddy** | Reverse proxy + Basic Auth (Bab 6, opsional). |
| `Caddy.Dockerfile` | **Caddy** | Membungkus `Caddyfile` ke image Caddy agar bisa di-deploy. |
| `.env.example` | semua | Daftar semua variabel + di mana diisi. |
| `.gitignore`, `.dockerignore` | — | Higiene repo & build. |
| `scripts/test_connection.py` | klien | Verifikasi tracking + auth + artifact (Bab 7–8). |

## Dua topologi deploy

**Topologi 1 — tanpa Caddy (cepat, TANPA auth — jangan untuk publik):**
Service MLflow langsung diberi domain publik. Railway mengisi `$PORT`.

**Topologi 2 — dengan Caddy (disarankan, ADA Basic Auth):**
- Service **MLflow**: TIDAK punya domain publik. Set variabel `PORT=5000`.
- Service **Caddy**: punya domain publik, meneruskan ke
  `mlflow.railway.internal:5000`.

## Ringkasan deploy (rujuk panduan untuk detail)

1. Letakkan folder ini di repo, lalu `git push` (Bab 5.4).
2. Railway → **New → Deploy from GitHub repo** → set **Root Directory =
   `mlflow-server`** (Bab 5.5).
3. Tambah **PostgreSQL** (Bab 5.6) dan **MinIO** + bucket + Volume (Bab 5.7, 5.10).
4. Isi **Variables** pada service MLflow sesuai `.env.example` bagian (A) / Bab 5.8.
5. (Topologi 2) Tambah service **Caddy** (Dockerfile Path = `Caddy.Dockerfile`),
   isi `AUTH_USER` & `AUTH_PASSWORD_HASH`, set `PORT=5000` di MLflow, generate
   domain HANYA di Caddy (Bab 6).
6. Generate domain (Bab 5.11) → itulah `MLFLOW_TRACKING_URI` Anda.

Buat hash password Caddy (tanpa instalasi Caddy lokal):

```bash
docker run --rm caddy:2-alpine caddy hash-password --plaintext 'passwordRahasiaAnda'
```

## Verifikasi

```bash
export MLFLOW_TRACKING_URI="https://<domain-anda>.up.railway.app"
export MLFLOW_TRACKING_USERNAME="<user>"
export MLFLOW_TRACKING_PASSWORD="<password>"
pip install mlflow==3.11.1
python scripts/test_connection.py
```

## Menghubungkan ke RiskFinder

Lihat **`INTEGRATION-RiskFinder.md`** — cara menyinkronkan server ini dengan
proyek RiskFinder yang sudah ter-deploy (intinya: set `MLFLOW_TRACKING_URI` +
kredensial pada **ds-service**; frontend tidak perlu diubah).
