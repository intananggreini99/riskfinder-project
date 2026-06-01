-- =====================================================================
--  RiskFinder · File 02 — Skema SNOWFLAKE hasil testing Credit Analysis
--  (schema: analytics)
--
--  Bentuk snowflake: tabel fakta di pusat, dimensi dinormalisasi menjadi
--  sub-dimensi (mis. dim_borrower → dim_sex, dim_education, dim_marriage,
--  dim_age_group; dim_model → dim_preprocessing, dim_algorithm).
--
--      dim_sex ─┐
--   dim_education┤
--   dim_marriage ┼─< dim_borrower >─┐
--   dim_age_group┘                  │
--                                    ├─< fact_credit_testing >── dim_date
--   dim_algorithm ─< dim_model >─────┘            │
--   dim_preprocessing ┘                            └──1:1── credit_input_detail
-- =====================================================================

-- ============ SUB-DIMENSI (lookup ternormalisasi) ============
CREATE TABLE IF NOT EXISTS analytics.dim_sex (
    sex_key   SMALLINT PRIMARY KEY,   -- = kode SEX (1,2)
    sex_label VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_education (
    education_key   SMALLINT PRIMARY KEY,  -- = kode EDUCATION (1..4)
    education_label VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.dim_marriage (
    marriage_key   SMALLINT PRIMARY KEY,   -- = kode MARRIAGE (1..3)
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
    preprocessing_id  VARCHAR(64) UNIQUE NOT NULL,   -- selaras ds.preprocessing_artifact
    filename          VARCHAR(255),
    n_features        INT
);

-- ============ DIMENSI UTAMA (snowflaked) ============
CREATE TABLE IF NOT EXISTS analytics.dim_model (
    model_key         SERIAL PRIMARY KEY,
    model_id          VARCHAR(64) UNIQUE NOT NULL,    -- selaras ds.model_artifact
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
    date_key   INT PRIMARY KEY,          -- format YYYYMMDD
    full_date  DATE NOT NULL,
    day        SMALLINT,
    month      SMALLINT,
    year       SMALLINT,
    quarter    SMALLINT
);

-- ============ TABEL FAKTA ============
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

-- Detail input mentah (23 fitur) — relasi 1:1 dengan fakta (degenerate dimension)
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
