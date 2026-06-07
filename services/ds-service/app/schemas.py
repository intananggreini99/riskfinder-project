"""Skema Pydantic request/response untuk Data Scientist Service RiskFinder."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RFBaseModel(BaseModel):
    """
    Base model untuk seluruh schema RiskFinder.

    Pydantic v2 memiliki protected namespace default untuk nama field
    yang diawali dengan "model_". Karena aplikasi RiskFinder memang
    memakai nama field seperti model_version dan model_size, konfigurasi
    protected_namespaces dikosongkan agar tidak muncul UserWarning.
    """

    model_config = ConfigDict(protected_namespaces=())


# ---------- Auth ----------
class TokenResponse(RFBaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


# ---------- Build Model / ML Flow ----------
class RunConfig(RFBaseModel):
    test_size: float = 0.30
    random_state: int = 42
    n_trials: int = 80
    model_version: Optional[str] = ""


class ArtifactInfo(RFBaseModel):
    preprocessing: str
    model: str
    preprocessing_size: Optional[str] = None
    model_size: Optional[str] = None


class DatasetInfo(RFBaseModel):
    name: str
    rows: int


class RunResult(RFBaseModel):
    run_id: str
    metrics: Dict[str, Any]
    artifacts: ArtifactInfo
    datasets: List[DatasetInfo]


# ---------- Build Model · MLflow Projects ----------
class ProjectFile(RFBaseModel):
    """Satu berkas pada MLflow Project yang ditampilkan di web UI."""

    path: str
    label: str
    language: str = "python"
    editable: bool = False
    content: str


class ProjectSpec(RFBaseModel):
    """Spesifikasi MLflow Project dan parameter default halaman Service ML Flow."""

    name: str
    entry_points: List[str]
    default_params: Dict[str, Any]
    files: List[ProjectFile]
    mlflow_ui_url: str
    experiment: str
    dataset_file: str
    next_version: str


class ProjectRunRequest(RFBaseModel):
    entry_point: str = "main"
    test_size: float = 0.30
    random_state: int = 42
    n_trials: int = 80
    model_version: Optional[str] = ""


class ProjectRunResult(RFBaseModel):
    status: str
    command: str
    logs: str
    run_id: Optional[str] = None
    mlflow_run_id: Optional[str] = None
    version: Optional[str] = None
    algorithm: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    artifacts: Optional[ArtifactInfo] = None
    datasets: List[DatasetInfo] = Field(default_factory=list)
    mlflow_ui_url: Optional[str] = None
    error: Optional[str] = None


# ---------- Monitoring · Management ----------
class ModelOut(RFBaseModel):
    id: str
    name: str
    algo: Optional[str] = None
    roc_auc: Optional[float] = None
    created: Optional[str] = None


class PrepOut(RFBaseModel):
    id: str
    name: str
    features: Optional[int] = None
    created: Optional[str] = None


class PairCreate(RFBaseModel):
    model: str
    preprocessing: str


class PairOut(RFBaseModel):
    id: str
    name: str
    model: str
    preprocessing: str
    active: bool = False
    metrics: Dict[str, Any] = Field(default_factory=dict)


# ---------- Monitoring · Evaluation ----------
class EvaluationOut(RFBaseModel):
    pair_name: str
    learning_curve: List[Dict[str, Any]]
    confusion_matrix: Dict[str, int]
    classification_report: List[Dict[str, Any]]
    roc_auc_train: float
    roc_auc_test: float
    gap: float


# ---------- Monitoring · Deployment ----------
class TestingHistoryItem(RFBaseModel):
    id: str
    score: float
    label: int
    at: str
    input: Dict[str, Any]


class TestingHistoryOut(RFBaseModel):
    avg_score: float
    total: int
    history: List[TestingHistoryItem]