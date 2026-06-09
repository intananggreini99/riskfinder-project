"""Router prediksi (testing) — Divisi Credit Analysis.

Setiap entry = satu baris testing → preprocessing identik training →
prediksi model aktif (model_final.pkl di Docker Volume) → simpan ke PostgreSQL snowflake.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import get_current_user
from ..schemas import CreditInput, PredictionOut, BatchInput, BatchOut, BatchResultItem
from ..ml import inference
from .. import persistence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["predict"])


def _to_plain_dict(data: CreditInput) -> dict:
    """Kompatibel untuk Pydantic v2 dan v1."""
    if hasattr(data, "model_dump"):
        return data.model_dump()
    return data.dict()


def _save_testing_or_raise(db: Session, raw: dict, result: dict, analyst_username: str) -> int:
    """Simpan hasil testing ke database.

    Error insert DB tidak boleh ditelan, karena UI Credit Analysis harus tahu
    apakah hasil prediksi benar-benar sudah tersimpan di tabel analytics.
    """
    try:
        testing_id = persistence.save_testing(db, raw, result, analyst_username)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Prediksi berhasil, tetapi gagal menyimpan hasil testing ke database. "
            "analyst=%s raw=%s result=%s",
            analyst_username,
            raw,
            result,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Prediksi berhasil, tetapi gagal disimpan ke database. "
                f"Detail: {exc}"
            ),
        ) from exc

    if testing_id is None:
        logger.error(
            "save_testing tidak mengembalikan testing_id. analyst=%s raw=%s result=%s",
            analyst_username,
            raw,
            result,
        )
        raise HTTPException(
            status_code=500,
            detail="Prediksi berhasil, tetapi testing_id tidak terbentuk di database.",
        )

    return int(testing_id)


@router.post("", response_model=PredictionOut)
def predict_single(
    data: CreditInput,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    raw = _to_plain_dict(data)

    try:
        res = inference.predict_one(raw)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=424, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Prediksi single gagal. analyst=%s raw=%s", user.get("username"), raw)
        raise HTTPException(status_code=500, detail=f"Prediksi gagal: {exc}") from exc

    testing_id = _save_testing_or_raise(db, raw, res, user["username"])

    return PredictionOut(
        prediction_label=res["prediction_label"],
        prediction_score=res["prediction_score"],
        status=res["status"],
        testing_id=testing_id,
    )


@router.post("/batch", response_model=BatchOut)
def predict_batch(
    body: BatchInput,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not body.borrowers:
        raise HTTPException(status_code=400, detail="Daftar peminjam kosong.")

    results: list[BatchResultItem] = []
    active_model = None

    for idx, borrower in enumerate(body.borrowers, start=1):
        raw = _to_plain_dict(borrower)

        try:
            res = inference.predict_one(raw)
            active_model = res.get("_model_file") or active_model
        except FileNotFoundError as exc:
            raise HTTPException(status_code=424, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception(
                "Prediksi batch gagal pada peminjam ke-%s. analyst=%s raw=%s",
                idx,
                user.get("username"),
                raw,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Prediksi gagal pada peminjam ke-{idx}: {exc}",
            ) from exc

        testing_id = _save_testing_or_raise(db, raw, res, user["username"])

        results.append(
            BatchResultItem(
                input=raw,
                prediction_label=res["prediction_label"],
                prediction_score=res["prediction_score"],
                status=res["status"],
                testing_id=testing_id,
            )
        )

    return BatchOut(results=results, active_model=active_model)