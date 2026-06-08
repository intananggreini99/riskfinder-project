# Sinkronisasi `mlflow-server` ke Proyek RiskFinder

Panduan ini menyambungkan server MLflow (paket ini) ke proyek **RiskFinder**
yang **sudah selesai sampai tahap deploy** (Vercel + Railway/Render + Neon +
Docker Hub, sesuai *RiskFinder-Panduan-Deploy.docx*).

---

## 0. Hal terpenting yang harus dipahami dulu

**Frontend (`frontend.zip`) TIDAK berbicara langsung ke MLflow.**

Halaman *Service ML Flow* (`src/pages/ServiceMLFlow.jsx`) memanggil **ds-service**:

```js
await dsApi.post('/mlflow/pull-data')   // -> ds-service
await dsApi.post('/mlflow/run', config) // -> ds-service
```

Jadi alur sebenarnya adalah:

```
Frontend (Vercel)  ──►  ds-service (Railway)  ──►  MLflow Tracking Server (Railway)
                          (pakai MLFLOW_TRACKING_URI + Basic Auth)
```

**Konsekuensinya, "menyinkronkan `mlflow-server`" = 3 hal:**
1. Menaruh folder `mlflow-server/` di repo dan men-deploy-nya sebagai service baru.
2. Mengisi `MLFLOW_TRACKING_URI` (+ kredensial Basic Auth) pada **ds-service**
   yang **sudah ter-deploy**.
3. **Frontend tidak perlu diubah** (ia hanya menghubungi ds-service).

> Di *RiskFinder-Panduan-Deploy.docx* Bab 5.3 & Lampiran A, `MLFLOW_TRACKING_URI`
> memang sudah terdaftar sebagai variabel **opsional** pada ds-service —
> sebelumnya dibiarkan kosong. Langkah di bawah inilah yang mengisinya.

---

## 1. Peta repo setelah sinkronisasi

`frontend.zip` hanya berisi folder `frontend/`. Repo RiskFinder lengkap Anda
(yang dipakai untuk deploy backend) kira-kira seperti ini — tambahkan
`mlflow-server/` di **root**, sejajar dengan `frontend/` dan `services/`:

```
riskfinder/
├── frontend/                 # dari frontend.zip — sudah deploy ke Vercel
├── services/
│   ├── ds-service/           # sudah deploy ke Railway  ← yang akan kita sambungkan
│   └── ca-service/           # sudah deploy ke Railway
├── db/init/                  # SQL sudah dijalankan di Neon
└── mlflow-server/            # ◄── BARU (paket ini)
    ├── Dockerfile
    ├── requirements.txt
    ├── entrypoint.sh
    ├── Caddyfile
    ├── Caddy.Dockerfile
    └── scripts/test_connection.py
```

**Dua pilihan penempatan:**
- **Opsi B1 — Monorepo (disarankan):** taruh `mlflow-server/` di dalam repo
  RiskFinder. Saat membuat service Railway, set **Root Directory = `mlflow-server`**
  agar Railway menemukan Dockerfile-nya.
- **Opsi B2 — Repo sendiri:** dorong `mlflow-server/` ke repo terpisah
  `mlflow-server.git` (persis Bab 5.4 panduan MLflow). Root Directory dibiarkan
  default. Pilih ini bila ingin siklus deploy MLflow lepas dari RiskFinder.

---

## 2. Tambahkan folder ke repo & push

```bash
# dari root repo RiskFinder Anda
cp -r mlflow-server ./           # salin folder dari paket ini
git add mlflow-server
git commit -m "Tambah MLflow tracking server (Metode B) + integrasi RiskFinder"
git push origin main
```

---

## 3. Deploy MLflow + Postgres + Artifact store (ringkas — detail di Bab 5)

1. **Railway → New Project → Deploy from GitHub repo** → pilih repo RiskFinder.
   - Buka service → **Settings → Root Directory = `mlflow-server`** (Opsi B1).
   - Railway mendeteksi `Dockerfile` dan mulai build (build pertama boleh gagal
     karena variabel belum ada — wajar, Bab 5.5).
2. **Tambah PostgreSQL**: project yang sama → **New → Database → PostgreSQL** (Bab 5.6).
3. **Tambah MinIO**: template MinIO → buat bucket `mlflow-artifacts` → lampirkan
   **Volume** ke direktori data MinIO (Bab 5.7 & 5.10).
   *Alternatif:* Cloudflare R2 (egress gratis, tanpa MinIO + Volume).
4. **Isi Variables pada service MLflow** (Bab 5.8 / `.env.example` bagian A):

   | Variabel | Nilai |
   | --- | --- |
   | `MLFLOW_BACKEND_STORE_URI` | `${{Postgres.DATABASE_URL}}` (pastikan `postgresql://`) |
   | `MLFLOW_ARTIFACTS_DESTINATION` | `s3://mlflow-artifacts` |
   | `MLFLOW_S3_ENDPOINT_URL` | `http://minio.railway.internal:9000` |
   | `AWS_ACCESS_KEY_ID` | `${{MinIO.MINIO_ROOT_USER}}` |
   | `AWS_SECRET_ACCESS_KEY` | `${{MinIO.MINIO_ROOT_PASSWORD}}` |
   | `AWS_DEFAULT_REGION` | `us-east-1` |

   `entrypoint.sh` sudah otomatis memperbaiki `postgres://` → `postgresql://`,
   jadi gotcha Bab 5.6 tertangani sendiri.

---

## 4. (Disarankan) Pasang Basic Auth via Caddy — Topologi 2

Tanpa proteksi, domain publik MLflow terbuka bebas. Pasang Caddy di depannya.

1. **Service MLflow**: JANGAN generate domain publik. Set variabel **`PORT=5000`**
   (agar cocok dengan target `mlflow.railway.internal:5000` di `Caddyfile`).
2. **Buat service Caddy** di project yang sama, dari repo yang sama:
   - **Root Directory = `mlflow-server`**
   - **Settings → Dockerfile Path = `Caddy.Dockerfile`**
3. **Buat hash password** (tanpa instalasi Caddy lokal):
   ```bash
   docker run --rm caddy:2-alpine caddy hash-password --plaintext 'passwordRahasiaAnda'
   ```
4. **Variables service Caddy**: `AUTH_USER` dan `AUTH_PASSWORD_HASH` (hash di atas).
5. **Generate Domain HANYA di service Caddy** (Bab 5.11). Domain Caddy inilah
   `MLFLOW_TRACKING_URI` Anda.

> Lewati seluruh Bab ini bila memilih Topologi 1 (MLflow generate domain sendiri,
> tanpa auth). Tidak disarankan untuk endpoint publik.

---

## 5. ◆ INTI SINKRONISASI — Sambungkan ds-service ke MLflow

Pada service **ds-service** RiskFinder yang **sudah ter-deploy**, buka tab
**Variables** lalu tambah/ubah:

| Key | Value | Catatan |
| --- | --- | --- |
| `MLFLOW_TRACKING_URI` | `https://<domain-caddy-atau-mlflow>.up.railway.app` | **Tanpa** garis miring di akhir |
| `MLFLOW_TRACKING_USERNAME` | `<AUTH_USER>` | Hanya bila pakai Caddy (Topologi 2) |
| `MLFLOW_TRACKING_PASSWORD` | `<password plaintext>` | Hanya bila pakai Caddy (Topologi 2) |

Lalu **Redeploy ds-service** agar variabel ikut terbaca.

**Mengapa di ds-service, bukan frontend?** Karena halaman *Service ML Flow*
memanggil `dsApi` → endpoint `/mlflow/*` ditangani ds-service, dan ds-service
itulah yang menjadi *klien* MLflow. MLflow membaca
`MLFLOW_TRACKING_USERNAME`/`PASSWORD` untuk Basic Auth secara otomatis (Bab 7).

**Pastikan kode ds-service memang memakai variabel ini.** Di dalam handler
`/mlflow/run` (atau saat startup), seharusnya ada pola seperti:

```python
import os, mlflow

uri = os.environ.get("MLFLOW_TRACKING_URI")
if uri:
    mlflow.set_tracking_uri(uri)
    # MLFLOW_TRACKING_USERNAME/PASSWORD dibaca otomatis oleh MLflow untuk Basic Auth
    mlflow.set_experiment("riskfinder-build-model")
    with mlflow.start_run(run_name=config.get("model_version") or "baseline"):
        mlflow.log_param("test_size", config["test_size"])
        mlflow.log_metric("roc_auc", metrics["roc_auc_test"])
        mlflow.sklearn.log_model(model, name="model")  # otomatis lewat --serve-artifacts
```

Bila ds-service belum memuat blok semacam ini, tambahkan — itulah yang membuat
run benar-benar terkirim ke server MLflow Anda.

---

## 6. (Opsional) Tautkan UI MLflow dari frontend

Frontend **tidak butuh** perubahan agar pipeline berfungsi. Tapi bila Anda ingin
tombol "Buka MLflow UI" di halaman *Service ML Flow*, tambahkan satu env Vercel
**`VITE_MLFLOW_UI_URL`** = domain MLflow/Caddy, lalu render sebuah link:

```jsx
{import.meta.env.VITE_MLFLOW_UI_URL && (
  <a href={import.meta.env.VITE_MLFLOW_UI_URL} target="_blank" rel="noreferrer"
     className="btn-ghost btn-sm">Buka MLflow UI</a>
)}
```

Ini murni kosmetik (buka UI di tab baru); alur build model tetap lewat ds-service.

---

## 7. Verifikasi sinkronisasi (Bab 8)

1. **UI langsung:** buka domain MLflow/Caddy di browser → login Basic Auth →
   UI MLflow muncul.
2. **Skrip uji (lokal):**
   ```bash
   export MLFLOW_TRACKING_URI="https://<domain-anda>.up.railway.app"
   export MLFLOW_TRACKING_USERNAME="<user>"
   export MLFLOW_TRACKING_PASSWORD="<password>"
   pip install mlflow==3.11.1
   python mlflow-server/scripts/test_connection.py
   ```
   Sukses → run `connection-check` muncul di UI dan artifact bisa diunduh.
3. **End-to-end via aplikasi:** login **Data Scientist** di domain Vercel →
   *Build Model / Service ML Flow* → **Jalankan Pipeline** → cek run baru muncul
   di UI MLflow, dan *Monitoring* terisi (tersimpan di Neon schema `analytics`).

---

## 8. Peta variabel (siapa diisi di mana)

| Variabel | MLflow svc | Caddy svc | ds-service | Lokal/CI |
| --- | :---: | :---: | :---: | :---: |
| `MLFLOW_BACKEND_STORE_URI` | ✅ | | | |
| `MLFLOW_ARTIFACTS_DESTINATION` | ✅ | | | |
| `MLFLOW_S3_ENDPOINT_URL` | ✅ | | | |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | ✅ | | | |
| `AWS_DEFAULT_REGION` | ✅ | | | |
| `PORT=5000` (Topologi 2) | ✅ | (auto) | | |
| `AUTH_USER` / `AUTH_PASSWORD_HASH` | | ✅ | | |
| `MLFLOW_TRACKING_URI` | | | ✅ | ✅ |
| `MLFLOW_TRACKING_USERNAME` / `..._PASSWORD` | | | ✅ | ✅ |

---

## 9. Troubleshooting cepat (gabungan Bab 8 MLflow + Bab 9 RiskFinder)

| Gejala | Sebab | Solusi |
| --- | --- | --- |
| `401 Unauthorized` dari ds-service ke MLflow | user/password Basic Auth salah/tak ada di ds-service | Set `MLFLOW_TRACKING_USERNAME`/`PASSWORD` di ds-service, redeploy |
| `502` saat buka domain MLflow/Caddy | server tak bind `0.0.0.0:$PORT`, atau target Caddy salah port | MLflow bind `--host 0.0.0.0 --port $PORT`; set `PORT=5000` di MLflow agar cocok `:5000` di Caddyfile |
| Error dialek/koneksi DB (`postgres`) | skema masih `postgres://` | Sudah ditangani `entrypoint.sh`; bila perlu buat variabel skema `postgresql://` |
| Artifact gagal upload/timeout | endpoint/kredensial S3 salah, atau tanpa `--serve-artifacts` | Cek `MLFLOW_S3_ENDPOINT_URL` + key; `--serve-artifacts` sudah aktif di entrypoint |
| `ENOTFOUND *.railway.internal` | service beda project/environment | Pastikan MLflow, Postgres, MinIO, Caddy **satu project & environment** |
| UI MLflow kosong dari aplikasi | ds-service belum `set_tracking_uri()` / belum redeploy | Tambahkan blok kode Bab 5 + isi `MLFLOW_TRACKING_URI` + redeploy ds-service |

---

## 10. Checklist sinkronisasi

- [ ] Folder `mlflow-server/` ada di repo & ter-push.
- [ ] Service MLflow ter-deploy (Root Directory = `mlflow-server`).
- [ ] PostgreSQL & MinIO (bucket + Volume) terpasang di project yang sama.
- [ ] Variables service MLflow terisi (backend store, artifacts, S3 keys).
- [ ] (Topologi 2) Caddy ter-deploy, `AUTH_*` terisi, `PORT=5000` di MLflow,
      domain publik hanya di Caddy.
- [ ] **ds-service**: `MLFLOW_TRACKING_URI` (+ `USERNAME`/`PASSWORD`) terisi &
      sudah **redeploy**.
- [ ] `scripts/test_connection.py` sukses (run + artifact).
- [ ] End-to-end dari Vercel: Build Model → run muncul di MLflow → Monitoring terisi.
