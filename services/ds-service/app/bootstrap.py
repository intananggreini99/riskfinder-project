"""Bootstrap database untuk Data Scientist Sistem.

Sama seperti ca-service: pada database terkelola (Neon/Railway/Render) skrip
``db/init/*.sql`` tidak dijalankan, sehingga skema ``ds`` dan ``analytics``
belum ada dan ``create_all`` gagal (``schema "ds"/"analytics" does not exist``).

Modul ini membuat skema yang dibutuhkan, lalu seluruh tabel ORM, lalu mengisi
katalog default V1 (training run, artifact, pasangan, evaluasi) agar halaman
Monitoring & Model Evaluation membaca dari PostgreSQL — bukan dari konstanta
demo di frontend. Tabel fakta ``analytics`` ditulis oleh ca-service; di sini
cukup memastikan skema/tabelnya ada agar query monitoring tidak gagal.

Seluruh operasi idempotent dan aman dijalankan pada setiap startup.
"""
from __future__ import annotations

from sqlalchemy import text

from .database import Base, engine
from . import models  # noqa: F401  (registrasi seluruh tabel ke metadata)

_SCHEMAS = ("ds", "analytics")

# DDL kanonik skema analytics — identik dengan db/init/02_snowflake.sql.
# Disertakan agar bila ds-service melakukan bootstrap lebih dulu pada database
# kosong (Neon), tabel fakta tetap dibuat dengan kolom lengkap sehingga INSERT
# dari ca-service tidak gagal. Idempotent (CREATE TABLE IF NOT EXISTS).
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

# Katalog default V1 + evaluasi — selaras dengan db/init/04_model_evaluation_seed.sql.
# Memakai parameter agar JSONB ter-cast dengan benar lewat driver.
_SEED_RUN = """
INSERT INTO ds.training_run (
    run_id, mlflow_run_id, test_size, random_state, n_trials, algorithm,
    roc_auc_train, roc_auc_test, gap_train_test, f1_score,
    precision_score, recall_score, accuracy_score
) VALUES (
    'run_notebook_v1', 'notebook_v1', 0.30, 42, 80, 'GradientBoosting',
    0.8123, 0.7841, 0.0282, 0.4880, 0.6590, 0.3880, 0.8209
)
ON CONFLICT (run_id) DO NOTHING;
"""

_SEED_PREP = """
INSERT INTO ds.preprocessing_artifact (preprocessing_id, filename, run_id, n_features)
VALUES ('preprocessing_V1', 'preprocessing_artifacts_V1.pkl', 'run_notebook_v1', 23)
ON CONFLICT (preprocessing_id) DO NOTHING;
"""

_SEED_MODEL = """
INSERT INTO ds.model_artifact (model_id, filename, run_id, algorithm, roc_auc)
VALUES ('model_V1', 'best_credit_model_V1.pkl', 'run_notebook_v1', 'GradientBoosting', 0.7841)
ON CONFLICT (model_id) DO NOTHING;
"""

_SEED_PAIR = """
INSERT INTO ds.model_pair (
    pair_id, name, model_id, preprocessing_id, is_active,
    roc_auc_train, roc_auc_test, gap_train_test, f1_score,
    precision_score, recall_score, accuracy_score
) VALUES (
    'pair_model_V1_preprocessing_V1', 'Model_V1 + preprocessing_V1',
    'model_V1', 'preprocessing_V1', TRUE,
    0.8123, 0.7841, 0.0282, 0.4880, 0.6590, 0.3880, 0.8209
)
ON CONFLICT (pair_id) DO NOTHING;
"""

_SEED_EVAL = """
INSERT INTO ds.model_evaluation (
    evaluation_id, run_id, model_id, pair_id,
    learning_curve, confusion_matrix, classification_report,
    roc_auc_train, roc_auc_test, gap_train_test
) VALUES (
    'evaluation_V1', 'run_notebook_v1', 'model_V1', 'pair_model_V1_preprocessing_V1',
    CAST(:learning_curve AS jsonb), CAST(:confusion_matrix AS jsonb),
    CAST(:classification_report AS jsonb),
    0.8123, 0.7841, 0.0282
)
ON CONFLICT (evaluation_id) DO NOTHING;
"""

_LEARNING_CURVE = (
    '[{"size":"20%","train":0.872,"test":0.741},'
    '{"size":"36%","train":0.851,"test":0.758},'
    '{"size":"52%","train":0.836,"test":0.769},'
    '{"size":"68%","train":0.824,"test":0.776},'
    '{"size":"84%","train":0.817,"test":0.781},'
    '{"size":"100%","train":0.812,"test":0.784}]'
)
_CONFUSION_MATRIX = '{"tn":6612,"fp":397,"fn":1213,"tp":768}'
_CLASSIFICATION_REPORT = (
    '[{"label":"0 \u00b7 Non-Default","precision":0.845,"recall":0.943,"f1":0.891,"support":7009},'
    '{"label":"1 \u00b7 Default","precision":0.659,"recall":0.388,"f1":0.488,"support":1981}]'
)


def ensure_schemas() -> None:
    """Buat skema + tabel kanonik analytics bila belum ada (idempotent)."""
    with engine.begin() as conn:
        for schema in _SCHEMAS:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        conn.execute(text(_ANALYTICS_DDL))


def seed_catalog() -> None:
    """Isi katalog default V1 agar halaman Monitoring memakai data PostgreSQL."""
    with engine.begin() as conn:
        conn.execute(text(_SEED_RUN))
        conn.execute(text(_SEED_PREP))
        conn.execute(text(_SEED_MODEL))
        conn.execute(text(_SEED_PAIR))
        conn.execute(
            text(_SEED_EVAL),
            {
                "learning_curve": _LEARNING_CURVE,
                "confusion_matrix": _CONFUSION_MATRIX,
                "classification_report": _CLASSIFICATION_REPORT,
            },
        )


def init_db() -> None:
    """Urutan bootstrap: skema → tabel → seed katalog."""
    ensure_schemas()
    Base.metadata.create_all(bind=engine)
    seed_catalog()
