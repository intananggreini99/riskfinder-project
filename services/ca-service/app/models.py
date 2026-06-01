"""Model ORM SQLAlchemy (skema snowflake) — Credit Analysis Sistem.

Menulis hasil testing ke analytics.fact_credit_testing dan dimensi terkait.
"""
from sqlalchemy import (
    Column, String, Integer, SmallInteger, BigInteger, Numeric, DateTime, ForeignKey, Date
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .database import Base

SCHEMA = "analytics"


class DimSex(Base):
    __tablename__ = "dim_sex"; __table_args__ = {"schema": SCHEMA}
    sex_key = Column(SmallInteger, primary_key=True)
    sex_label = Column(String(20), nullable=False)


class DimEducation(Base):
    __tablename__ = "dim_education"; __table_args__ = {"schema": SCHEMA}
    education_key = Column(SmallInteger, primary_key=True)
    education_label = Column(String(30), nullable=False)


class DimMarriage(Base):
    __tablename__ = "dim_marriage"; __table_args__ = {"schema": SCHEMA}
    marriage_key = Column(SmallInteger, primary_key=True)
    marriage_label = Column(String(20), nullable=False)


class DimAgeGroup(Base):
    __tablename__ = "dim_age_group"; __table_args__ = {"schema": SCHEMA}
    age_group_key = Column(SmallInteger, primary_key=True)
    age_group_label = Column(String(20), nullable=False)
    min_age = Column(SmallInteger)
    max_age = Column(SmallInteger)


class DimAlgorithm(Base):
    __tablename__ = "dim_algorithm"; __table_args__ = {"schema": SCHEMA}
    algorithm_key = Column(Integer, primary_key=True, autoincrement=True)
    algorithm_name = Column(String(64), unique=True, nullable=False)


class DimPreprocessing(Base):
    __tablename__ = "dim_preprocessing"; __table_args__ = {"schema": SCHEMA}
    preprocessing_key = Column(Integer, primary_key=True, autoincrement=True)
    preprocessing_id = Column(String(64), unique=True, nullable=False)
    filename = Column(String(255))
    n_features = Column(Integer)


class DimModel(Base):
    __tablename__ = "dim_model"; __table_args__ = {"schema": SCHEMA}
    model_key = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String(64), unique=True, nullable=False)
    filename = Column(String(255))
    algorithm_key = Column(Integer, ForeignKey(f"{SCHEMA}.dim_algorithm.algorithm_key"))
    preprocessing_key = Column(Integer, ForeignKey(f"{SCHEMA}.dim_preprocessing.preprocessing_key"))


class DimBorrower(Base):
    __tablename__ = "dim_borrower"; __table_args__ = {"schema": SCHEMA}
    borrower_key = Column(BigInteger, primary_key=True, autoincrement=True)
    limit_bal = Column(Numeric(14, 2), nullable=False)
    age = Column(SmallInteger, nullable=False)
    sex_key = Column(SmallInteger, ForeignKey(f"{SCHEMA}.dim_sex.sex_key"))
    education_key = Column(SmallInteger, ForeignKey(f"{SCHEMA}.dim_education.education_key"))
    marriage_key = Column(SmallInteger, ForeignKey(f"{SCHEMA}.dim_marriage.marriage_key"))
    age_group_key = Column(SmallInteger, ForeignKey(f"{SCHEMA}.dim_age_group.age_group_key"))


class DimDate(Base):
    __tablename__ = "dim_date"; __table_args__ = {"schema": SCHEMA}
    date_key = Column(Integer, primary_key=True)  # YYYYMMDD
    full_date = Column(Date, nullable=False)
    day = Column(SmallInteger)
    month = Column(SmallInteger)
    year = Column(SmallInteger)
    quarter = Column(SmallInteger)


class FactCreditTesting(Base):
    __tablename__ = "fact_credit_testing"; __table_args__ = {"schema": SCHEMA}
    testing_id = Column(BigInteger, primary_key=True, autoincrement=True)
    date_key = Column(Integer, ForeignKey(f"{SCHEMA}.dim_date.date_key"))
    borrower_key = Column(BigInteger, ForeignKey(f"{SCHEMA}.dim_borrower.borrower_key"))
    model_key = Column(Integer, ForeignKey(f"{SCHEMA}.dim_model.model_key"))
    prediction_label = Column(SmallInteger, nullable=False)
    prediction_score = Column(Numeric(6, 4), nullable=False)
    analyst_username = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CreditInputDetail(Base):
    __tablename__ = "credit_input_detail"; __table_args__ = {"schema": SCHEMA}
    testing_id = Column(BigInteger, ForeignKey(f"{SCHEMA}.fact_credit_testing.testing_id", ondelete="CASCADE"), primary_key=True)
    pay_0 = Column(SmallInteger); pay_2 = Column(SmallInteger); pay_3 = Column(SmallInteger)
    pay_4 = Column(SmallInteger); pay_5 = Column(SmallInteger); pay_6 = Column(SmallInteger)
    bill_amt1 = Column(Numeric(14, 2)); bill_amt2 = Column(Numeric(14, 2)); bill_amt3 = Column(Numeric(14, 2))
    bill_amt4 = Column(Numeric(14, 2)); bill_amt5 = Column(Numeric(14, 2)); bill_amt6 = Column(Numeric(14, 2))
    pay_amt1 = Column(Numeric(14, 2)); pay_amt2 = Column(Numeric(14, 2)); pay_amt3 = Column(Numeric(14, 2))
    pay_amt4 = Column(Numeric(14, 2)); pay_amt5 = Column(Numeric(14, 2)); pay_amt6 = Column(Numeric(14, 2))
    raw_json = Column(JSONB)
