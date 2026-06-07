"""Skema Pydantic (request/response) untuk Data Scientist Sistem."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


# ---------- Auth ----------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


# ---------- Build Model / ML Flow ----------
class RunConfig(BaseModel):
    test_size: float = 0.30
    random_state: int = 42
    n_trials: int = 80
    model_version: Optional[str] = ""


class ArtifactInfo(BaseModel):
    preprocessing: str
    model: str
    preprocessing_size: Optional[str] = None
    model_size: Optional[str] = None


class DatasetInfo(BaseModel):
    name: str
    rows: int


class RunResult(BaseModel):
    run_id: str
    metrics: Dict[str, Any]
    artifacts: ArtifactInfo
    datasets: List[DatasetInfo]


# ---------- Build Model · MLflow Projects (web UI MLflow) ----------
class ProjectFile(BaseModel):
    """Satu berkas pada MLflow Project yang ditampilkan & dapat diedit di web UI."""
    path: str                       # mis. "MLproject", "train_pipeline.py", "preprocessing.py"
    label: str                      # judul ramah untuk tab
    language: str = "python"        # python | yaml | text → untuk syntax highlight
    editable: bool = False
    content: str


class ProjectSpec(BaseModel):
    """Spesifikasi MLflow Project + parameter default untuk halaman Service ML Flow."""
    name: str
    entry_points: List[str]
    default_params: Dict[str, Any]
    files: List[ProjectFile]
    mlflow_ui_url: str
    experiment: str
    dataset_file: str
    next_version: str


class ProjectRunRequest(BaseModel):
    entry_point: str = "main"
    test_size: float = 0.30
    random_state: int = 42
    n_trials: int = 80
    model_version: Optional[str] = ""


class ProjectRunResult(BaseModel):
    status: str                     # success | error
    command: str                    # perintah `mlflow run ...` yang dieksekusi
    logs: str                       # gabungan stdout/stderr eksekusi
    run_id: Optional[str] = None
    mlflow_run_id: Optional[str] = None
    version: Optional[str] = None
    algorithm: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    artifacts: Optional[ArtifactInfo] = None
    datasets: List[DatasetInfo] = []
    mlflow_ui_url: Optional[str] = None
    error: Optional[str] = None


# ---------- Monitoring · Management ----------
class ModelOut(BaseModel):
    id: str
    name: str
    algo: Optional[str] = None
    roc_auc: Optional[float] = None
    created: Optional[str] = None


class PrepOut(BaseModel):
    id: str
    name: str
    features: Optional[int] = None
    created: Optional[str] = None


class PairCreate(BaseModel):
    model: str
    preprocessing: str


class PairOut(BaseModel):
    id: str
    name: str
    model: str
    preprocessing: str
    active: bool = False
    metrics: Dict[str, Any] = {}


# ---------- Monitoring · Evaluation ----------
class EvaluationOut(BaseModel):
    pair_name: str
    learning_curve: List[Dict[str, Any]]
    confusion_matrix: Dict[str, int]
    classification_report: List[Dict[str, Any]]
    roc_auc_train: float
    roc_auc_test: float
    gap: float


# ---------- Monitoring · Deployment ----------
class TestingHistoryItem(BaseModel):
    id: str
    score: float
    label: int
    at: str
    input: Dict[str, Any]


class TestingHistoryOut(BaseModel):
    avg_score: float
    total: int
    history: List[TestingHistoryItem]
