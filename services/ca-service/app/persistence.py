"""Persistensi hasil testing ke schema snowflake `analytics`.

Tabel yang ditulis:
- analytics.dim_date
- analytics.dim_preprocessing
- analytics.dim_algorithm
- analytics.dim_model
- analytics.dim_borrower
- analytics.fact_credit_testing
- analytics.credit_input_detail
"""
import json
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .config import settings


def _to_decimal(value, places: str = "0.0001") -> Decimal:
    return Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _age_group_key(age: int) -> int:
    if age <= 24:
        return 0
    if age <= 34:
        return 1
    if age <= 44:
        return 2
    if age <= 54:
        return 3
    return 4


def _normalize_education(value: int) -> int:
    return value if value in (1, 2, 3, 4) else 4


def _normalize_marriage(value: int) -> int:
    return value if value in (1, 2, 3) else 3


def _ensure_lookup_rows(db: Session) -> None:
    """Pastikan lookup snowflake tersedia.

    Ini penting karena jika 03_seed.sql belum dijalankan, insert borrower
    akan gagal akibat foreign key ke dim_sex/dim_education/dim_marriage/dim_age_group.
    """

    sex_rows = [
        models.DimSex(sex_key=1, sex_label="Laki-laki"),
        models.DimSex(sex_key=2, sex_label="Perempuan"),
    ]

    education_rows = [
        models.DimEducation(education_key=1, education_label="Pascasarjana"),
        models.DimEducation(education_key=2, education_label="Sarjana"),
        models.DimEducation(education_key=3, education_label="SMA"),
        models.DimEducation(education_key=4, education_label="Lainnya"),
    ]

    marriage_rows = [
        models.DimMarriage(marriage_key=1, marriage_label="Menikah"),
        models.DimMarriage(marriage_key=2, marriage_label="Lajang"),
        models.DimMarriage(marriage_key=3, marriage_label="Lainnya"),
    ]

    age_group_rows = [
        models.DimAgeGroup(age_group_key=0, age_group_label="<25", min_age=0, max_age=24),
        models.DimAgeGroup(age_group_key=1, age_group_label="25-34", min_age=25, max_age=34),
        models.DimAgeGroup(age_group_key=2, age_group_label="35-44", min_age=35, max_age=44),
        models.DimAgeGroup(age_group_key=3, age_group_label="45-54", min_age=45, max_age=54),
        models.DimAgeGroup(age_group_key=4, age_group_label="55+", min_age=55, max_age=200),
    ]

    for row in sex_rows + education_rows + marriage_rows + age_group_rows:
        db.merge(row)

    db.flush()


def _ensure_algorithm(db: Session, algorithm_name: str = "GradientBoosting") -> int:
    row = db.execute(
        select(models.DimAlgorithm)
        .where(models.DimAlgorithm.algorithm_name == algorithm_name)
    ).scalar_one_or_none()

    if row:
        return int(row.algorithm_key)

    row = models.DimAlgorithm(algorithm_name=algorithm_name)
    db.add(row)
    db.flush()
    return int(row.algorithm_key)


def _ensure_date(db: Session, dt: datetime) -> int:
    date_key = int(dt.strftime("%Y%m%d"))

    row = db.get(models.DimDate, date_key)
    if row:
        return date_key

    db.add(
        models.DimDate(
            date_key=date_key,
            full_date=dt.date(),
            day=dt.day,
            month=dt.month,
            year=dt.year,
            quarter=(dt.month - 1) // 3 + 1,
        )
    )
    db.flush()
    return date_key


def _active_artifact_identity() -> tuple[str, str, str, str]:
    """Ambil identitas model/preprocessing aktif.

    Return:
        model_id, model_file, preprocessing_id, preprocessing_file
    """

    model_file = settings.DEFAULT_MODEL_FILE
    prep_file = settings.DEFAULT_PREP_FILE
    model_id = "model_V1"
    prep_id = "preprocessing_V1"

    if os.path.exists(settings.ACTIVE_POINTER):
        try:
            with open(settings.ACTIVE_POINTER, encoding="utf-8") as f:
                ptr = json.load(f)

            model_file = ptr.get("model_file") or model_file
            prep_file = ptr.get("preprocessing_file") or prep_file
        except Exception:
            pass

    if model_file:
        version = (
            model_file
            .replace("best_credit_model_", "")
            .replace(".pkl", "")
        )
        model_id = f"model_{version}"

    if prep_file:
        version = (
            prep_file
            .replace("preprocessing_artifacts_", "")
            .replace(".pkl", "")
        )
        prep_id = f"preprocessing_{version}"

    return model_id, model_file, prep_id, prep_file


def _ensure_model(db: Session) -> int:
    model_id, model_file, prep_id, prep_file = _active_artifact_identity()

    prep = db.execute(
        select(models.DimPreprocessing)
        .where(models.DimPreprocessing.preprocessing_id == prep_id)
    ).scalar_one_or_none()

    if not prep:
        prep = models.DimPreprocessing(
            preprocessing_id=prep_id,
            filename=prep_file,
            n_features=23,
        )
        db.add(prep)
        db.flush()
    else:
        prep.filename = prep_file
        if prep.n_features is None:
            prep.n_features = 23
        db.flush()

    algorithm_key = _ensure_algorithm(db, "GradientBoosting")

    model = db.execute(
        select(models.DimModel)
        .where(models.DimModel.model_id == model_id)
    ).scalar_one_or_none()

    if not model:
        model = models.DimModel(
            model_id=model_id,
            filename=model_file,
            algorithm_key=algorithm_key,
            preprocessing_key=prep.preprocessing_key,
        )
        db.add(model)
        db.flush()
    else:
        model.filename = model_file
        model.algorithm_key = algorithm_key
        model.preprocessing_key = prep.preprocessing_key
        db.flush()

    return int(model.model_key)


def save_testing(db: Session, raw: dict, result: dict, analyst: str) -> int:
    """Simpan satu hasil testing dan return testing_id.

    Fungsi ini sengaja melempar exception jika penyimpanan gagal.
    Router /predict akan mengubahnya menjadi HTTP 500 supaya frontend tidak
    menampilkan hasil palsu seolah-olah sudah tersimpan.
    """

    _ensure_lookup_rows(db)

    now = datetime.now(timezone.utc)
    date_key = _ensure_date(db, now)
    model_key = _ensure_model(db)

    borrower = models.DimBorrower(
        limit_bal=_to_decimal(raw["LIMIT_BAL"], "0.01"),
        age=int(raw["AGE"]),
        sex_key=int(raw["SEX"]),
        education_key=_normalize_education(int(raw["EDUCATION"])),
        marriage_key=_normalize_marriage(int(raw["MARRIAGE"])),
        age_group_key=_age_group_key(int(raw["AGE"])),
    )
    db.add(borrower)
    db.flush()

    fact = models.FactCreditTesting(
        date_key=date_key,
        borrower_key=borrower.borrower_key,
        model_key=model_key,
        prediction_label=int(result["prediction_label"]),
        prediction_score=_to_decimal(result["prediction_score"], "0.0001"),
        analyst_username=analyst,
    )
    db.add(fact)
    db.flush()

    detail = models.CreditInputDetail(
        testing_id=fact.testing_id,
        pay_0=int(raw["PAY_0"]),
        pay_2=int(raw["PAY_2"]),
        pay_3=int(raw["PAY_3"]),
        pay_4=int(raw["PAY_4"]),
        pay_5=int(raw["PAY_5"]),
        pay_6=int(raw["PAY_6"]),
        bill_amt1=_to_decimal(raw["BILL_AMT1"], "0.01"),
        bill_amt2=_to_decimal(raw["BILL_AMT2"], "0.01"),
        bill_amt3=_to_decimal(raw["BILL_AMT3"], "0.01"),
        bill_amt4=_to_decimal(raw["BILL_AMT4"], "0.01"),
        bill_amt5=_to_decimal(raw["BILL_AMT5"], "0.01"),
        bill_amt6=_to_decimal(raw["BILL_AMT6"], "0.01"),
        pay_amt1=_to_decimal(raw["PAY_AMT1"], "0.01"),
        pay_amt2=_to_decimal(raw["PAY_AMT2"], "0.01"),
        pay_amt3=_to_decimal(raw["PAY_AMT3"], "0.01"),
        pay_amt4=_to_decimal(raw["PAY_AMT4"], "0.01"),
        pay_amt5=_to_decimal(raw["PAY_AMT5"], "0.01"),
        pay_amt6=_to_decimal(raw["PAY_AMT6"], "0.01"),
        raw_json=raw,
    )
    db.add(detail)

    db.commit()
    db.refresh(fact)

    return int(fact.testing_id)