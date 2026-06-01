"""Persistensi hasil testing ke skema SNOWFLAKE (analytics).

Menyelesaikan key dimensi (snowflaked) lalu menulis fakta + detail input.
"""
import json
import os
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .config import settings


def _age_group_key(age: int) -> int:
    bins = [(0, 24, 0), (25, 34, 1), (35, 44, 2), (45, 54, 3), (55, 200, 4)]
    for lo, hi, key in bins:
        if lo <= age <= hi:
            return key
    return 4


def _ensure_date(db: Session, dt: datetime) -> int:
    date_key = int(dt.strftime("%Y%m%d"))
    if not db.get(models.DimDate, date_key):
        db.add(models.DimDate(
            date_key=date_key, full_date=dt.date(),
            day=dt.day, month=dt.month, year=dt.year, quarter=(dt.month - 1) // 3 + 1,
        ))
        db.flush()
    return date_key


def _ensure_model(db: Session) -> int | None:
    """Pastikan dim_model untuk pasangan aktif tersedia; return model_key."""
    model_file = settings.DEFAULT_MODEL_FILE
    model_id = "model_V1"
    prep_id = "preprocessing_V1"
    prep_file = settings.DEFAULT_PREP_FILE
    if os.path.exists(settings.ACTIVE_POINTER):
        try:
            with open(settings.ACTIVE_POINTER) as f:
                ptr = json.load(f)
            model_file = ptr.get("model_file") or model_file
            prep_file = ptr.get("preprocessing_file") or prep_file
            # turunkan id dari nama file: best_credit_model_V1.pkl -> model_V1
            if model_file:
                v = model_file.replace("best_credit_model_", "").replace(".pkl", "")
                model_id = f"model_{v}"
            if prep_file:
                v = prep_file.replace("preprocessing_artifacts_", "").replace(".pkl", "")
                prep_id = f"preprocessing_{v}"
        except Exception:
            pass

    prep = db.execute(select(models.DimPreprocessing).where(models.DimPreprocessing.preprocessing_id == prep_id)).scalar_one_or_none()
    if not prep:
        prep = models.DimPreprocessing(preprocessing_id=prep_id, filename=prep_file)
        db.add(prep); db.flush()

    dm = db.execute(select(models.DimModel).where(models.DimModel.model_id == model_id)).scalar_one_or_none()
    if not dm:
        dm = models.DimModel(model_id=model_id, filename=model_file, preprocessing_key=prep.preprocessing_key)
        db.add(dm); db.flush()
    return dm.model_key


def save_testing(db: Session, raw: dict, result: dict, analyst: str) -> int:
    """Simpan satu hasil testing; return testing_id."""
    now = datetime.utcnow()

    # 1) dimensi borrower (snowflaked: sex/education/marriage/age_group sebagai key)
    borrower = models.DimBorrower(
        limit_bal=raw["LIMIT_BAL"], age=raw["AGE"],
        sex_key=raw["SEX"],
        education_key=(raw["EDUCATION"] if raw["EDUCATION"] in (1, 2, 3, 4) else 4),
        marriage_key=(raw["MARRIAGE"] if raw["MARRIAGE"] in (1, 2, 3) else 3),
        age_group_key=_age_group_key(int(raw["AGE"])),
    )
    db.add(borrower); db.flush()

    date_key = _ensure_date(db, now)
    model_key = _ensure_model(db)

    # 2) fakta
    fact = models.FactCreditTesting(
        date_key=date_key, borrower_key=borrower.borrower_key, model_key=model_key,
        prediction_label=result["prediction_label"], prediction_score=result["prediction_score"],
        analyst_username=analyst,
    )
    db.add(fact); db.flush()

    # 3) detail input mentah (degenerate dimension)
    db.add(models.CreditInputDetail(
        testing_id=fact.testing_id,
        pay_0=raw["PAY_0"], pay_2=raw["PAY_2"], pay_3=raw["PAY_3"],
        pay_4=raw["PAY_4"], pay_5=raw["PAY_5"], pay_6=raw["PAY_6"],
        bill_amt1=raw["BILL_AMT1"], bill_amt2=raw["BILL_AMT2"], bill_amt3=raw["BILL_AMT3"],
        bill_amt4=raw["BILL_AMT4"], bill_amt5=raw["BILL_AMT5"], bill_amt6=raw["BILL_AMT6"],
        pay_amt1=raw["PAY_AMT1"], pay_amt2=raw["PAY_AMT2"], pay_amt3=raw["PAY_AMT3"],
        pay_amt4=raw["PAY_AMT4"], pay_amt5=raw["PAY_AMT5"], pay_amt6=raw["PAY_AMT6"],
        raw_json=raw,
    ))
    db.commit()
    return int(fact.testing_id)
