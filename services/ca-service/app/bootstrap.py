"""Bootstrap database untuk Credit Analysis Sistem.

Saat di-deploy ke database terkelola (mis. Neon/Railway/Render), skrip
``db/init/*.sql`` TIDAK ikut dijalankan — skrip itu hanya berlaku untuk
container PostgreSQL lokal melalui ``/docker-entrypoint-initdb.d``. Akibatnya
skema ``analytics`` belum ada, dan ``Base.metadata.create_all`` gagal dengan
``schema "analytics" does not exist`` karena SQLAlchemy hanya menerbitkan
``CREATE TABLE``, bukan ``CREATE SCHEMA``.

Modul ini membuat skema yang dibutuhkan, lalu seluruh tabel ORM, lalu mengisi
dimensi lookup (snowflake) yang menjadi acuan foreign key pada
``persistence.save_testing``. Tanpa seed dimensi tersebut, INSERT borrower akan
melanggar constraint FK sehingga hasil prediksi tidak pernah tersimpan.

Seluruh operasi bersifat idempotent dan aman dijalankan pada setiap startup.
"""
from __future__ import annotations

from sqlalchemy import text

from .database import Base, engine
from . import models  # noqa: F401  (memastikan seluruh tabel ter-registrasi di metadata)

# Skema yang harus ada sebelum create_all. ``analytics`` wajib untuk fakta
# testing; ``ds`` disertakan agar database yang sama tetap konsisten bila
# ds-service belum sempat melakukan bootstrap.
_SCHEMAS = ("analytics", "ds")

# DDL kanonik skema analytics — identik dengan db/init/02_snowflake.sql.
# Dijalankan sebelum create_all agar tabel fakta selalu memiliki kolom lengkap
# tanpa bergantung pada urutan startup antar service (create_all hanya membuat
# tabel yang belum ada, sehingga tidak akan menambah kolom yang hilang).
_ANALYTICS_DDL = """
CREATE TABLE IF NOT EXISTS analytics.dim_sex (
    sex_key   SMALLINT PRIMARY KEY,
    sex_label VARCHAR(20) NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics.dim_education (
    education_key   SMALLINT PRIMARY KEY,
    education_label VARCHAR(30) NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics.dim_marriage (
    marriage_key   SMALLINT PRIMARY KEY,
    marriage_label VARCHAR(20) NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics.dim_age_group (
    age_group_key   SMALLINT PRIMARY KEY,
    age_group_label VARCHAR(20) NOT NULL,
    min_age         SMALLINT,
    max_age         SMALLINT
);
CREATE TABLE IF NOT EXISTS analytics.dim_algorithm (
    algorithm_key  SERIAL PRIMARY KEY,
    algorithm_name VARCHAR(64) UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics.dim_preprocessing (
    preprocessing_key SERIAL PRIMARY KEY,
    preprocessing_id  VARCHAR(64) UNIQUE NOT NULL,
    filename          VARCHAR(255),
    n_features        INT
);
CREATE TABLE IF NOT EXISTS analytics.dim_model (
    model_key         SERIAL PRIMARY KEY,
    model_id          VARCHAR(64) UNIQUE NOT NULL,
    filename          VARCHAR(255),
    algorithm_key     INT REFERENCES analytics.dim_algorithm(algorithm_key),
    preprocessing_key INT REFERENCES analytics.dim_preprocessing(preprocessing_key)
);
CREATE TABLE IF NOT EXISTS analytics.dim_borrower (
    borrower_key   BIGSERIAL PRIMARY KEY,
    limit_bal      NUMERIC(14,2) NOT NULL,
    age            SMALLINT      NOT NULL,
    sex_key        SMALLINT REFERENCES analytics.dim_sex(sex_key),
    education_key  SMALLINT REFERENCES analytics.dim_education(education_key),
    marriage_key   SMALLINT REFERENCES analytics.dim_marriage(marriage_key),
    age_group_key  SMALLINT REFERENCES analytics.dim_age_group(age_group_key)
);
CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key   INT PRIMARY KEY,
    full_date  DATE NOT NULL,
    day        SMALLINT,
    month      SMALLINT,
    year       SMALLINT,
    quarter    SMALLINT
);
CREATE TABLE IF NOT EXISTS analytics.fact_credit_testing (
    testing_id        BIGSERIAL PRIMARY KEY,
    date_key          INT      REFERENCES analytics.dim_date(date_key),
    borrower_key      BIGINT   REFERENCES analytics.dim_borrower(borrower_key),
    model_key         INT      REFERENCES analytics.dim_model(model_key),
    prediction_label  SMALLINT NOT NULL CHECK (prediction_label IN (0, 1)),
    prediction_score  NUMERIC(6,4) NOT NULL,
    analyst_username  VARCHAR(64),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS analytics.credit_input_detail (
    testing_id  BIGINT PRIMARY KEY REFERENCES analytics.fact_credit_testing(testing_id) ON DELETE CASCADE,
    pay_0  SMALLINT, pay_2 SMALLINT, pay_3 SMALLINT, pay_4 SMALLINT, pay_5 SMALLINT, pay_6 SMALLINT,
    bill_amt1 NUMERIC(14,2), bill_amt2 NUMERIC(14,2), bill_amt3 NUMERIC(14,2),
    bill_amt4 NUMERIC(14,2), bill_amt5 NUMERIC(14,2), bill_amt6 NUMERIC(14,2),
    pay_amt1  NUMERIC(14,2), pay_amt2  NUMERIC(14,2), pay_amt3  NUMERIC(14,2),
    pay_amt4  NUMERIC(14,2), pay_amt5  NUMERIC(14,2), pay_amt6  NUMERIC(14,2),
    raw_json  JSONB
);
CREATE INDEX IF NOT EXISTS idx_fact_created ON analytics.fact_credit_testing(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fact_label   ON analytics.fact_credit_testing(prediction_label);
"""

# Seed dimensi lookup — selaras dengan db/init/03_seed.sql.
_SEED_SQL = """
INSERT INTO analytics.dim_sex (sex_key, sex_label) VALUES
    (1, 'Laki-laki'), (2, 'Perempuan')
ON CONFLICT (sex_key) DO NOTHING;

INSERT INTO analytics.dim_education (education_key, education_label) VALUES
    (1, 'Pascasarjana'), (2, 'Sarjana'), (3, 'SMA'), (4, 'Lainnya')
ON CONFLICT (education_key) DO NOTHING;

INSERT INTO analytics.dim_marriage (marriage_key, marriage_label) VALUES
    (1, 'Menikah'), (2, 'Lajang'), (3, 'Lainnya')
ON CONFLICT (marriage_key) DO NOTHING;

INSERT INTO analytics.dim_age_group (age_group_key, age_group_label, min_age, max_age) VALUES
    (0, '<25',    0,  24),
    (1, '25-34',  25, 34),
    (2, '35-44',  35, 44),
    (3, '45-54',  45, 54),
    (4, '55+',    55, 200)
ON CONFLICT (age_group_key) DO NOTHING;

INSERT INTO analytics.dim_algorithm (algorithm_name) VALUES
    ('GradientBoosting'), ('XGBoost'), ('AdaBoost'), ('RandomForest')
ON CONFLICT (algorithm_name) DO NOTHING;
"""


def ensure_schemas() -> None:
    """Buat skema + tabel kanonik analytics bila belum ada (idempotent)."""
    with engine.begin() as conn:
        for schema in _SCHEMAS:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        conn.execute(text(_ANALYTICS_DDL))


def seed_dimensions() -> None:
    """Isi dimensi lookup snowflake yang menjadi acuan FK fakta testing."""
    with engine.begin() as conn:
        conn.execute(text(_SEED_SQL))


def init_db() -> None:
    """Urutan bootstrap: skema → tabel → seed dimensi."""
    ensure_schemas()
    Base.metadata.create_all(bind=engine)
    seed_dimensions()
