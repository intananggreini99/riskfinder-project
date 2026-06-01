"""Router prediksi (testing) — Divisi Credit Analysis.

Setiap entry = satu baris testing → preprocessing identik training →
prediksi model aktif (model_final.pkl di Docker Volume) → simpan ke PostgreSQL snowflake.
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
def predict_single(data: CreditInput, db: Session = Depends(get_db), user=Depends(get_current_user)):
    raw = data.model_dump()
    try:
        res = inference.predict_one(raw)
    except FileNotFoundError as e:
        raise HTTPException(status_code=424, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediksi gagal: {e}")

    testing_id = None
    try:
        testing_id = persistence.save_testing(db, raw, res, user["username"])
    except Exception:
        db.rollback()  # gagal simpan tidak menggagalkan prediksi

    return PredictionOut(
        prediction_label=res["prediction_label"], prediction_score=res["prediction_score"],
        status=res["status"], testing_id=testing_id,
    )


@router.post("/batch", response_model=BatchOut)
def predict_batch(body: BatchInput, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not body.borrowers:
        raise HTTPException(status_code=400, detail="Daftar peminjam kosong.")

    results: list[BatchResultItem] = []
    active_model = None
    for b in body.borrowers:
        raw = b.model_dump()
        try:
            res = inference.predict_one(raw)
            active_model = res.get("_model_file")
        except FileNotFoundError as e:
            raise HTTPException(status_code=424, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Prediksi gagal: {e}")

        testing_id = None
        try:
            testing_id = persistence.save_testing(db, raw, res, user["username"])
        except Exception:
            db.rollback()

        results.append(BatchResultItem(
            input=raw, prediction_label=res["prediction_label"],
            prediction_score=res["prediction_score"], status=res["status"], testing_id=testing_id,
        ))

    return BatchOut(results=results, active_model=active_model)
