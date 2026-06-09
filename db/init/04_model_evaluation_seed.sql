-- =====================================================================
--  RiskFinder · File 04 — Seed katalog V1 & evaluasi model dari notebook
--  Aman dijalankan berulang pada Neon/PostgreSQL yang sudah terdeploy.
-- =====================================================================

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

-- Katalog default V1 agar halaman Management dan ModelEvaluation membaca dari PostgreSQL.
INSERT INTO ds.training_run (
    run_id, mlflow_run_id, test_size, random_state, n_trials, algorithm,
    roc_auc_train, roc_auc_test, gap_train_test, f1_score,
    precision_score, recall_score, accuracy_score
) VALUES (
    'run_notebook_v1', 'notebook_v1', 0.30, 42, 80, 'GradientBoosting',
    0.8123, 0.7841, 0.0282, 0.4880,
    0.6590, 0.3880, 0.8209
)
ON CONFLICT (run_id) DO UPDATE SET
    algorithm = EXCLUDED.algorithm,
    roc_auc_train = EXCLUDED.roc_auc_train,
    roc_auc_test = EXCLUDED.roc_auc_test,
    gap_train_test = EXCLUDED.gap_train_test,
    f1_score = EXCLUDED.f1_score,
    precision_score = EXCLUDED.precision_score,
    recall_score = EXCLUDED.recall_score,
    accuracy_score = EXCLUDED.accuracy_score;

INSERT INTO ds.preprocessing_artifact (preprocessing_id, filename, run_id, n_features)
VALUES ('preprocessing_V1', 'preprocessing_artifacts_V1.pkl', 'run_notebook_v1', 23)
ON CONFLICT (preprocessing_id) DO UPDATE SET
    filename = EXCLUDED.filename,
    run_id = EXCLUDED.run_id,
    n_features = EXCLUDED.n_features;

INSERT INTO ds.model_artifact (model_id, filename, run_id, algorithm, roc_auc)
VALUES ('model_V1', 'best_credit_model_V1.pkl', 'run_notebook_v1', 'GradientBoosting', 0.7841)
ON CONFLICT (model_id) DO UPDATE SET
    filename = EXCLUDED.filename,
    run_id = EXCLUDED.run_id,
    algorithm = EXCLUDED.algorithm,
    roc_auc = EXCLUDED.roc_auc;

-- Jaga unique index uq_single_active_pair: nonaktifkan dulu pasangan lain sebelum menjadikan V1 aktif.
UPDATE ds.model_pair SET is_active = FALSE WHERE is_active = TRUE AND pair_id <> 'pair_model_V1_preprocessing_V1';

INSERT INTO ds.model_pair (
    pair_id, name, model_id, preprocessing_id, is_active,
    roc_auc_train, roc_auc_test, gap_train_test, f1_score,
    precision_score, recall_score, accuracy_score
) VALUES (
    'pair_model_V1_preprocessing_V1', 'Model_V1 + preprocessing_V1',
    'model_V1', 'preprocessing_V1', TRUE,
    0.8123, 0.7841, 0.0282, 0.4880,
    0.6590, 0.3880, 0.8209
)
ON CONFLICT (pair_id) DO UPDATE SET
    name = EXCLUDED.name,
    model_id = EXCLUDED.model_id,
    preprocessing_id = EXCLUDED.preprocessing_id,
    is_active = EXCLUDED.is_active,
    roc_auc_train = EXCLUDED.roc_auc_train,
    roc_auc_test = EXCLUDED.roc_auc_test,
    gap_train_test = EXCLUDED.gap_train_test,
    f1_score = EXCLUDED.f1_score,
    precision_score = EXCLUDED.precision_score,
    recall_score = EXCLUDED.recall_score,
    accuracy_score = EXCLUDED.accuracy_score;

INSERT INTO ds.model_evaluation (
    evaluation_id, run_id, model_id, pair_id,
    learning_curve, confusion_matrix, classification_report,
    roc_auc_train, roc_auc_test, gap_train_test
) VALUES (
    'evaluation_V1', 'run_notebook_v1', 'model_V1', 'pair_model_V1_preprocessing_V1',
    '[
      {"size":"20%","train":0.872,"test":0.741},
      {"size":"36%","train":0.851,"test":0.758},
      {"size":"52%","train":0.836,"test":0.769},
      {"size":"68%","train":0.824,"test":0.776},
      {"size":"84%","train":0.817,"test":0.781},
      {"size":"100%","train":0.812,"test":0.784}
    ]'::jsonb,
    '{"tn":6612,"fp":397,"fn":1213,"tp":768}'::jsonb,
    '[
      {"label":"0 · Non-Default","precision":0.845,"recall":0.943,"f1":0.891,"support":7009},
      {"label":"1 · Default","precision":0.659,"recall":0.388,"f1":0.488,"support":1981}
    ]'::jsonb,
    0.8123, 0.7841, 0.0282
)
ON CONFLICT (evaluation_id) DO UPDATE SET
    run_id = EXCLUDED.run_id,
    model_id = EXCLUDED.model_id,
    pair_id = EXCLUDED.pair_id,
    learning_curve = EXCLUDED.learning_curve,
    confusion_matrix = EXCLUDED.confusion_matrix,
    classification_report = EXCLUDED.classification_report,
    roc_auc_train = EXCLUDED.roc_auc_train,
    roc_auc_test = EXCLUDED.roc_auc_test,
    gap_train_test = EXCLUDED.gap_train_test;
