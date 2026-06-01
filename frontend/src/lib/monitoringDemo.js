// Data contoh untuk halaman Monitoring saat backend belum aktif.
// Struktur identik dengan response endpoint /monitoring/* pada FastAPI.

export const DEMO_MODELS = [
  { id: 'model_V1', name: 'best_credit_model_V1.pkl', algo: 'GradientBoosting', roc_auc: 0.7841, created: '2025-05-20' },
  { id: 'model_V3', name: 'best_credit_model_V3.pkl', algo: 'XGBoost', roc_auc: 0.7795, created: '2025-05-24' },
]

export const DEMO_PREP = [
  { id: 'preprocessing_V1', name: 'preprocessing_artifacts_V1.pkl', features: 21, created: '2025-05-20' },
  { id: 'preprocessing_V2', name: 'preprocessing_artifacts_V2.pkl', features: 19, created: '2025-05-23' },
]

export const DEMO_PAIRS = [
  {
    id: 'pair_1',
    name: 'Model_V1 + preprocessing_V1',
    model: 'model_V1',
    preprocessing: 'preprocessing_V1',
    active: true,
    metrics: { roc_auc_train: 0.8123, roc_auc_test: 0.7841, gap: 0.0282, f1: 0.5402, precision: 0.6612, recall: 0.6217, accuracy: 0.8203 },
  },
]

export const DEMO_TESTING = {
  avg_score: 0.6432,
  total: 6,
  history: [
    { id: 't6', score: 0.8421, label: 1, at: '2025-05-28 14:21', input: { LIMIT_BAL: 20000, AGE: 24, PAY_0: 2, EDUCATION: 3, MARRIAGE: 2 } },
    { id: 't5', score: 0.7233, label: 1, at: '2025-05-28 11:02', input: { LIMIT_BAL: 50000, AGE: 29, PAY_0: 1, EDUCATION: 2, MARRIAGE: 2 } },
    { id: 't4', score: 0.7012, label: 1, at: '2025-05-27 16:44', input: { LIMIT_BAL: 80000, AGE: 41, PAY_0: 1, EDUCATION: 1, MARRIAGE: 1 } },
    { id: 't3', score: 0.5123, label: 0, at: '2025-05-27 10:15', input: { LIMIT_BAL: 150000, AGE: 38, PAY_0: 0, EDUCATION: 2, MARRIAGE: 1 } },
    { id: 't2', score: 0.4210, label: 0, at: '2025-05-26 09:30', input: { LIMIT_BAL: 200000, AGE: 45, PAY_0: -1, EDUCATION: 1, MARRIAGE: 1 } },
    { id: 't1', score: 0.3592, label: 0, at: '2025-05-25 13:58', input: { LIMIT_BAL: 320000, AGE: 52, PAY_0: -1, EDUCATION: 1, MARRIAGE: 1 } },
  ],
}

export const POSITIVE_THRESHOLD = 0.7
