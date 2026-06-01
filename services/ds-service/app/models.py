"""Model ORM SQLAlchemy untuk Data Scientist Sistem.

Memetakan katalog skema `ds` (run, artifact, pasangan, split) dan akses baca
fakta `analytics.fact_credit_testing` untuk halaman Monitoring.
"""
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, SmallInteger, BigInteger
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .database import Base


class TrainingRun(Base):
    __tablename__ = "training_run"
    __table_args__ = {"schema": "ds"}

    run_id = Column(String(64), primary_key=True)
    mlflow_run_id = Column(String(64))
    test_size = Column(Numeric(4, 2), default=0.30)
    random_state = Column(Integer, default=42)
    n_trials = Column(Integer, default=80)
    algorithm = Column(String(64))
    roc_auc_train = Column(Numeric(6, 4))
    roc_auc_test = Column(Numeric(6, 4))
    gap_train_test = Column(Numeric(6, 4))
    f1_score = Column(Numeric(6, 4))
    precision_score = Column(Numeric(6, 4))
    recall_score = Column(Numeric(6, 4))
    accuracy_score = Column(Numeric(6, 4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PreprocessingArtifact(Base):
    __tablename__ = "preprocessing_artifact"
    __table_args__ = {"schema": "ds"}

    preprocessing_id = Column(String(64), primary_key=True)
    filename = Column(String(255), nullable=False)
    run_id = Column(String(64), ForeignKey("ds.training_run.run_id"))
    n_features = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ModelArtifact(Base):
    __tablename__ = "model_artifact"
    __table_args__ = {"schema": "ds"}

    model_id = Column(String(64), primary_key=True)
    filename = Column(String(255), nullable=False)
    run_id = Column(String(64), ForeignKey("ds.training_run.run_id"))
    algorithm = Column(String(64))
    roc_auc = Column(Numeric(6, 4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ModelPair(Base):
    __tablename__ = "model_pair"
    __table_args__ = {"schema": "ds"}

    pair_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    model_id = Column(String(64), ForeignKey("ds.model_artifact.model_id"))
    preprocessing_id = Column(String(64), ForeignKey("ds.preprocessing_artifact.preprocessing_id"))
    is_active = Column(Boolean, default=False)
    roc_auc_train = Column(Numeric(6, 4))
    roc_auc_test = Column(Numeric(6, 4))
    gap_train_test = Column(Numeric(6, 4))
    f1_score = Column(Numeric(6, 4))
    precision_score = Column(Numeric(6, 4))
    recall_score = Column(Numeric(6, 4))
    accuracy_score = Column(Numeric(6, 4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DatasetSplit(Base):
    __tablename__ = "dataset_split"
    __table_args__ = {"schema": "ds"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("ds.training_run.run_id"))
    split_name = Column(String(32), nullable=False)
    filename = Column(String(255), nullable=False)
    n_rows = Column(Integer)
    dvc_path = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FactCreditTesting(Base):
    """Hanya untuk dibaca pada halaman Monitoring (ditulis oleh ca-service)."""
    __tablename__ = "fact_credit_testing"
    __table_args__ = {"schema": "analytics"}

    testing_id = Column(BigInteger, primary_key=True)
    date_key = Column(Integer)
    borrower_key = Column(BigInteger)
    model_key = Column(Integer)
    prediction_label = Column(SmallInteger, nullable=False)
    prediction_score = Column(Numeric(6, 4), nullable=False)
    analyst_username = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CreditInputDetail(Base):
    __tablename__ = "credit_input_detail"
    __table_args__ = {"schema": "analytics"}

    testing_id = Column(BigInteger, ForeignKey("analytics.fact_credit_testing.testing_id"), primary_key=True)
    raw_json = Column(JSONB)
