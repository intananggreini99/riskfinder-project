-- =====================================================================
-- RiskFinder · Migration
-- Add ds.model_evaluation table for ModelEvaluation.jsx
-- =====================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS ds;

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

COMMIT;