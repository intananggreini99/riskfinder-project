"""Router prediksi (testing) — Divisi Credit Analysis.

Setiap entry = satu baris testing:
input mentah → preprocessing inference → prediksi model aktif →
simpan hasil testing ke PostgreSQL/Neon schema analytics.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import get_current_user
from ..schemas import CreditInput, PredictionOut, BatchInput, BatchOut, BatchResultItem
from ..ml import inference
from .. import persistence

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("", response_model=PredictionOut)
def predict_single(
    data: CreditInput,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    raw = data.model_dump()

    try:
        res = inference.predict_one(raw)
    except FileNotFoundError as e:
        raise HTTPException(status_code=424, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediksi gagal: {e}")

    try:
        testing_id = persistence.save_testing(db, raw, res, user["username"])
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                "Prediksi berhasil, tetapi gagal menyimpan hasil testing ke "
                f"PostgreSQL/Neon schema analytics: {e}"
            ),
        )

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

    for index, borrower in enumerate(body.borrowers, start=1):
        raw = borrower.model_dump()

        try:
            res = inference.predict_one(raw)
            active_model = res.get("_model_file") or active_model
        except FileNotFoundError as e:
            raise HTTPException(status_code=424, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Prediksi gagal pada peminjam ke-{index}: {e}",
            )

        try:
            testing_id = persistence.save_testing(db, raw, res, user["username"])
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Prediksi peminjam ke-{index} berhasil, tetapi gagal menyimpan "
                    f"hasil testing ke PostgreSQL/Neon schema analytics: {e}"
                ),
            )

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