# RiskFinder — Credit Risk Analysis System

Sistem analisis risiko kredit end-to-end: memprediksi apakah seorang peminjam akan **gagal bayar (default)** menggunakan model klasifikasi (output `0` / `1`). Terdiri dari frontend React (deploy ke Vercel) dan dua backend FastAPI yang berjalan di **dua container Docker terpisah**, dengan JWT, DVC, MLflow, dan PostgreSQL berskema **snowflake**.

```
riskfinder/
├── frontend/            # React + Vite + TailwindCSS  → Vercel
├── services/
│   ├── ds-service/      # Container 1 · Data Scientist Sistem (port 8081)
│   └── ca-service/      # Container 2 · Credit Analysis Sistem (port 8082)
├── db/init/             # Skema snowflake PostgreSQL (auto-run)
├── .dvc/                # Konfigurasi DVC (remote Google Drive)
├── docker-compose.yml   # Orkestrasi backend + PostgreSQL + MLflow
└── docs/                # Panduan pengembangan & penggunaan (.docx)
```

## Arsitektur

| Komponen | Peran |
|---|---|
| **JWT** | Autentikasi login per divisi |
| **FastAPI** | Lapisan API (2 service terpisah) |
| **DVC** | Penyimpanan data tidak terstruktur (`.xls`, `.csv`, `.pkl`) — remote Google Drive |
| **PostgreSQL** | Database terstruktur, ERD **snowflake** |
| **Docker Volume** | Menyimpan artifact `.pkl` (preprocessing & model) bersama antar container |
| **MLflow** | Pelacakan eksperimen & metrik |

## Divisi & Kredensial

**Data Scientist Sistem** (build model, monitoring):
- `intan_anggreini99` / `intan999`
- `doa_ibu` / `ibuluvluv99`

**Credit Analysis Sistem** (entry data, prediksi):
- `kayla123` / `kaylasdt123`
- `dave77` / `davesdt77`

## Menjalankan Cepat (lokal, Windows 11 / Docker Desktop)

```bash
# 1) Backend + database + MLflow
copy .env.example .env          # lalu sesuaikan JWT_SECRET
docker compose up -d --build

# 2) Frontend
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

Backend: ds-service `http://localhost:8081/docs`, ca-service `http://localhost:8082/docs`.

## Deploy

- **Frontend → Vercel**: set env `VITE_DS_API_URL` & `VITE_CA_API_URL` ke URL publik backend.
- **Backend → Docker Hub + host container** (Railway/Render/VPS): `docker compose build && docker compose push`.

Langkah lengkap step-by-step ada di **`docs/RiskFinder-Panduan.docx`**.

## Pipeline ML — Build Model via MLflow Lokal

Menu **Build Model** pada Main Menu Data Scientist langsung mengecek dan mengalihkan browser ke
`http://localhost:5000` (atau nilai `VITE_MLFLOW_UI_URL`). Jika URL tidak dapat dijangkau,
frontend menampilkan pemberitahuan bahwa container MLflow lokal belum running. Jalankan:

```bash
docker compose up -d mlflow
```

Artifact default `best_credit_model_V1.pkl` dan `preprocessing_artifacts_V1.pkl` diambil dari
`Preprocessing_Modeling_EndToEnd_.ipynb` dan dibake ke image `ds-service` serta `ca-service`.
Agar Docker Volume lokal yang kosong tetap langsung berisi artifact V1, Dockerfile juga
menyediakan `/seed-artifacts` dan menyalinnya ke `/artifacts` saat container start.

Inference (`ca-service`) mereplikasi transformasi notebook: PAY_0→PAY_1, KNN imputation
untuk EDUCATION/MARRIAGE, IQR capping, feature engineering, OHE MARRIAGE, label encode SEX,
urutan `final_columns`, dan scaling memakai artifact preprocessing.

Evaluasi model pada halaman **ModelEvaluation.jsx** tidak memakai konstanta demo lagi; data
learning curve, confusion matrix, classification report, ROC AUC, dan gap dibaca dari tabel
`ds.model_evaluation` di PostgreSQL/Neon. Untuk database yang sudah terdeploy, jalankan:

```sql
-- Neon SQL Editor
-- Jalankan seluruh isi file ini
db/init/04_model_evaluation_seed.sql
```