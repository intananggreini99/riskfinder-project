-- =====================================================================
--  RiskFinder · Inisialisasi Database PostgreSQL
--  File 01 — schema, ekstensi, dan katalog Data Scientist Sistem
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS analytics;   -- skema snowflake hasil testing (Credit Analysis)
CREATE SCHEMA IF NOT EXISTS ds;          -- katalog model/dataset (Data Scientist)

-- ---------------------------------------------------------------------
--  KATALOG DATA SCIENTIST (skema: ds)
-- ---------------------------------------------------------------------

-- Setiap eksekusi pipeline Service ML Flow (Build Model)
CREATE TABLE IF NOT EXISTS ds.training_run (
    run_id           VARCHAR(64) PRIMARY KEY,
    mlflow_run_id    VARCHAR(64),
    test_size        NUMERIC(4,2)  NOT NULL DEFAULT 0.30,
    random_state     INT           NOT NULL DEFAULT 42,
    n_trials         INT           NOT NULL DEFAULT 80,
    algorithm        VARCHAR(64),
    roc_auc_train    NUMERIC(6,4),
    roc_auc_test     NUMERIC(6,4),
    gap_train_test   NUMERIC(6,4),
    f1_score         NUMERIC(6,4),
    precision_score  NUMERIC(6,4),
    recall_score     NUMERIC(6,4),
    accuracy_score   NUMERIC(6,4),
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- Artifact preprocessing (.pkl) yang dihasilkan
CREATE TABLE IF NOT EXISTS ds.preprocessing_artifact (
    preprocessing_id   VARCHAR(64) PRIMARY KEY,   -- mis. preprocessing_V1
    filename           VARCHAR(255) NOT NULL,      -- preprocessing_artifacts_V1.pkl
    run_id             VARCHAR(64) REFERENCES ds.training_run(run_id),
    n_features         INT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Artifact model (.pkl) yang dihasilkan
CREATE TABLE IF NOT EXISTS ds.model_artifact (
    model_id      VARCHAR(64) PRIMARY KEY,   -- mis. model_V1
    filename      VARCHAR(255) NOT NULL,      -- best_credit_model_V1.pkl
    run_id        VARCHAR(64) REFERENCES ds.training_run(run_id),
    algorithm     VARCHAR(64),
    roc_auc       NUMERIC(6,4),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Pasangan Model + Preprocessing
CREATE TABLE IF NOT EXISTS ds.model_pair (
    pair_id            VARCHAR(64) PRIMARY KEY,
    name               VARCHAR(255) NOT NULL,
    model_id           VARCHAR(64) REFERENCES ds.model_artifact(model_id),
    preprocessing_id   VARCHAR(64) REFERENCES ds.preprocessing_artifact(preprocessing_id),
    is_active          BOOLEAN NOT NULL DEFAULT FALSE,  -- pasangan deployment FastAPI
    roc_auc_train      NUMERIC(6,4),
    roc_auc_test       NUMERIC(6,4),
    gap_train_test     NUMERIC(6,4),
    f1_score           NUMERIC(6,4),
    precision_score    NUMERIC(6,4),
    recall_score       NUMERIC(6,4),
    accuracy_score     NUMERIC(6,4),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- Detail evaluasi model untuk halaman ModelEvaluation.jsx (sumber data PostgreSQL/Neon)
CREATE TABLE IF NOT EXISTS ds.model_evaluation (
    evaluation_id          VARCHAR(64) PRIMARY KEY,
    run_id                 VARCHAR(64) REFERENCES ds.training_run(run_id),
    model_id               VARCHAR(64) NOT NULL REFERENCES ds.model_artifact(model_id),
    pair_id                VARCHAR(64) REFERENCES ds.model_pair(pair_id),
    learning_curve         JSONB NOT NULL,
    confusion_matrix       JSONB NOT NULL,
    classification_report  JSONB NOT NULL,
    roc_auc_train          NUMERIC(6,4),
    roc_auc_test           NUMERIC(6,4),
    gap_train_test         NUMERIC(6,4),
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_model_evaluation_model
    ON ds.model_evaluation (model_id, created_at DESC);

-- Metadata set data train/test hasil preprocessing (juga di-track DVC)
CREATE TABLE IF NOT EXISTS ds.dataset_split (
    id            SERIAL PRIMARY KEY,
    run_id        VARCHAR(64) REFERENCES ds.training_run(run_id),
    split_name    VARCHAR(32) NOT NULL,   -- X_train | X_test | y_train | y_test
    filename      VARCHAR(255) NOT NULL,
    n_rows        INT,
    dvc_path      VARCHAR(255),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Memastikan hanya satu pasangan aktif pada satu waktu
CREATE UNIQUE INDEX IF NOT EXISTS uq_single_active_pair
    ON ds.model_pair (is_active) WHERE is_active = TRUE;
