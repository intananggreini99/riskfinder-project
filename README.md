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

## Pipeline ML

Preprocessing + modeling mengikuti `Preprocessing_Modeling_EndToEnd.ipynb` (Step 1–17):
drop ID & rename target, drop duplicates, tandai inkonsistensi → imputasi modus per-kelas,
IQR capping, feature extraction, encoding (OHE/label), binning AGE, feature selection
(korelasi + ANOVA), StandardScaler, lalu compare/tune/evaluasi model dan simpan
`preprocessing_artifacts.pkl` + `best_credit_model.pkl`. Inference (`ca-service`)
mereplikasi transformasi yang sama persis sebelum memprediksi.
