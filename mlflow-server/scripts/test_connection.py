#!/usr/bin/env python3
"""
mlflow-server/scripts/test_connection.py
=========================================
Verifikasi cepat koneksi ke MLflow Tracking Server (Bab 7 & 8 panduan).

Skrip ini:
  1) Membaca MLFLOW_TRACKING_URI, MLFLOW_TRACKING_USERNAME,
     MLFLOW_TRACKING_PASSWORD dari environment.
  2) Membuat 1 run percobaan + 1 param + 1 metric + 1 artifact kecil.
  3) Mengunduh kembali artifact tersebut (memastikan --serve-artifacts jalan).
  4) Mencetak ringkasan + URL run untuk dicek di UI.

Cara pakai (lokal):
    export MLFLOW_TRACKING_URI="https://<domain-anda>.up.railway.app"
    export MLFLOW_TRACKING_USERNAME="<user>"
    export MLFLOW_TRACKING_PASSWORD="<password>"
    pip install mlflow==3.11.1
    python scripts/test_connection.py

Sukses bila skrip selesai tanpa error dan run muncul di UI MLflow.
"""
import os
import sys
import tempfile
from pathlib import Path


def fail(msg: str) -> "None":
    print(f"\n❌  {msg}")
    sys.exit(1)


def main() -> None:
    uri = os.environ.get("MLFLOW_TRACKING_URI")
    user = os.environ.get("MLFLOW_TRACKING_USERNAME")
    pwd = os.environ.get("MLFLOW_TRACKING_PASSWORD")

    if not uri:
        fail("MLFLOW_TRACKING_URI belum diset. Lihat docstring di atas.")

    print("== Verifikasi koneksi MLflow ==")
    print(f"   Tracking URI : {uri}")
    print(f"   Basic Auth   : {'ya (user=' + user + ')' if user else 'tidak diset'}")

    try:
        import mlflow
    except ImportError:
        fail("Paket 'mlflow' belum terpasang. Jalankan: pip install mlflow==3.11.1")

    mlflow.set_tracking_uri(uri)

    # MLflow membaca MLFLOW_TRACKING_USERNAME/PASSWORD untuk Basic Auth otomatis.
    experiment_name = "riskfinder-connection-check"
    try:
        mlflow.set_experiment(experiment_name)
    except Exception as e:  # noqa: BLE001
        fail(
            "Gagal terhubung / autentikasi ke server.\n"
            f"   Detail: {e}\n"
            "   Cek: domain benar? Basic Auth (user/password) benar? "
            "Server Active/healthy?"
        )

    print("\n-> Membuat run percobaan…")
    with mlflow.start_run(run_name="connection-check") as run:
        mlflow.log_param("check", "ok")
        mlflow.log_metric("latency_dummy", 0.123)

        # Tulis artifact kecil lalu upload (menguji jalur --serve-artifacts).
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "hello.txt"
            f.write_text("RiskFinder ↔ MLflow: koneksi OK.\n", encoding="utf-8")
            mlflow.log_artifact(str(f))

        run_id = run.info.run_id
        print(f"   run_id = {run_id}")

    # Unduh kembali artifact untuk membuktikan proxy artifact bekerja.
    print("-> Mengunduh kembali artifact…")
    try:
        local_dir = mlflow.artifacts.download_artifacts(
            run_id=run_id, artifact_path="hello.txt"
        )
        content = Path(local_dir).read_text(encoding="utf-8").strip()
        print(f"   isi artifact: {content!r}")
    except Exception as e:  # noqa: BLE001
        fail(
            "Run tercatat, TAPI download artifact gagal.\n"
            f"   Detail: {e}\n"
            "   Cek: endpoint/kredensial S3 (MinIO/R2) & flag --serve-artifacts "
            "(Bab 8)."
        )

    base = uri.rstrip("/")
    print("\n✅  Sukses! Semua jalur (tracking + auth + artifact) berfungsi.")
    print(f"   Buka UI MLflow : {base}")
    print(f"   Eksperimen     : {experiment_name}")
    print(f"   Run            : {base}/#/experiments  (cari run 'connection-check')")


if __name__ == "__main__":
    main()
