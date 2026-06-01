"""Skema Pydantic — Credit Analysis Sistem."""
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class CreditInput(BaseModel):
    """23 fitur input (identik CreditInput notebook Step 18)."""
    LIMIT_BAL: float
    SEX: int = Field(..., ge=1, le=2)
    EDUCATION: int
    MARRIAGE: int
    AGE: int = Field(..., ge=18, le=120)
    PAY_0: int; PAY_2: int; PAY_3: int; PAY_4: int; PAY_5: int; PAY_6: int
    BILL_AMT1: float; BILL_AMT2: float; BILL_AMT3: float
    BILL_AMT4: float; BILL_AMT5: float; BILL_AMT6: float
    PAY_AMT1: float; PAY_AMT2: float; PAY_AMT3: float
    PAY_AMT4: float; PAY_AMT5: float; PAY_AMT6: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "LIMIT_BAL": 200000, "SEX": 2, "EDUCATION": 2, "MARRIAGE": 1, "AGE": 35,
                "PAY_0": 0, "PAY_2": 0, "PAY_3": 0, "PAY_4": 0, "PAY_5": 0, "PAY_6": 0,
                "BILL_AMT1": 38000, "BILL_AMT2": 41000, "BILL_AMT3": 39500,
                "BILL_AMT4": 30000, "BILL_AMT5": 25000, "BILL_AMT6": 20000,
                "PAY_AMT1": 4000, "PAY_AMT2": 3500, "PAY_AMT3": 3000,
                "PAY_AMT4": 2500, "PAY_AMT5": 2000, "PAY_AMT6": 1800,
            }
        }
    }


class PredictionOut(BaseModel):
    prediction_label: int
    prediction_score: float
    status: str
    testing_id: int | None = None


class BatchInput(BaseModel):
    borrowers: List[CreditInput]


class BatchResultItem(BaseModel):
    input: Dict[str, Any]
    prediction_label: int
    prediction_score: float
    status: str
    testing_id: int | None = None


class BatchOut(BaseModel):
    results: List[BatchResultItem]
    active_model: str | None = None
