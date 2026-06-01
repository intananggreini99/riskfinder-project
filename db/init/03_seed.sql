-- =====================================================================
--  RiskFinder · File 03 — Seed dimensi lookup (snowflake)
-- =====================================================================

INSERT INTO analytics.dim_sex (sex_key, sex_label) VALUES
    (1, 'Laki-laki'), (2, 'Perempuan')
ON CONFLICT (sex_key) DO NOTHING;

INSERT INTO analytics.dim_education (education_key, education_label) VALUES
    (1, 'Pascasarjana'), (2, 'Sarjana'), (3, 'SMA'), (4, 'Lainnya')
ON CONFLICT (education_key) DO NOTHING;

INSERT INTO analytics.dim_marriage (marriage_key, marriage_label) VALUES
    (1, 'Menikah'), (2, 'Lajang'), (3, 'Lainnya')
ON CONFLICT (marriage_key) DO NOTHING;

-- Selaras dengan binning AGE → AGE_GROUP pada artifact preprocessing
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
