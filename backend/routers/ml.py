"""ML API: AI price estimate (wraps the trained scikit-learn model)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from .. import database
from ..deps import optional_user
from ..ml import predict as ml
from ..models import PredictRequest

router = APIRouter(prefix="/api/ml", tags=["ml"])


@router.get("/status")
async def status():
    return {"ok": True, "available": ml.is_available(), "metrics": ml.metrics()}


@router.post("/predict")
async def predict(payload: PredictRequest, user: dict | None = Depends(optional_user)):
    if not ml.is_available():
        raise HTTPException(status_code=503, detail="Price estimator is unavailable.")

    result = ml.estimate(payload.model_dump())
    await database.predictions().insert_one({
        "user_id": user["_id"] if user else None,
        "features": payload.model_dump(),
        "predicted_price": result["price"],
        "created_at": datetime.now(timezone.utc),
    })

    return {
        "ok": True,
        "price": result["price"],
        "price_label": ml.short_inr(result["price"]),
        "price_full": ml.format_inr(result["price"]),
        "range_label": f"{ml.short_inr(result['price_low'])} - {ml.short_inr(result['price_high'])}",
        "range_low": result["price_low"],
        "range_high": result["price_high"],
    }
