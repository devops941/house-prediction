"""ML API: 100% pure AI price estimate and accurate city market calculation."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from .. import database
from ..deps import optional_user
from ..ml import ai_valuation
from ..ml import predict as ml
from ..models import PredictRequest

logger = logging.getLogger("nestquest.routers.ml")

router = APIRouter(prefix="/api/ml", tags=["ml"])


@router.get("/status")
async def status():
    return {
        "ok": True,
        "available": ml.is_available(),
        "metrics": ml.metrics(),
        "ai_engine": "Groq AI (openai/gpt-oss-120b)",
    }


@router.post("/predict")
async def predict(payload: PredictRequest, user: dict | None = Depends(optional_user)):
    data = payload.model_dump()
    try:
        result = await ai_valuation.estimate_property_value(data)
    except Exception as exc:
        logger.exception("AI prediction failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"AI Prediction error: {str(exc)}")

    price = result["price"]
    price_low = result.get("price_low") or round(price * 0.92)
    price_high = result.get("price_high") or round(price * 1.08)

    # Record purely predicted data in MongoDB if available
    try:
        await database.predictions().insert_one({
            "user_id": user["_id"] if user else None,
            "city": result.get("city") or payload.city,
            "locality": result.get("locality") or payload.locality,
            "features": data,
            "predicted_price": price,
            "rate_per_sqft": result.get("rate_per_sqft"),
            "estimated_rent_monthly": result.get("estimated_rent_monthly"),
            "ai_model": result.get("ai_model"),
            "created_at": datetime.now(timezone.utc),
        })
    except Exception as exc:
        logger.warning("Could not persist prediction to MongoDB: %s", exc)

    return {
        "ok": True,
        "price": price,
        "price_label": ml.short_inr(price),
        "price_full": ml.format_inr(price),
        "range_label": f"{ml.short_inr(price_low)} - {ml.short_inr(price_high)}",
        "range_low": price_low,
        "range_high": price_high,
        "city": result.get("city") or payload.city,
        "locality": result.get("locality") or payload.locality,
        "rate_per_sqft": result.get("rate_per_sqft"),
        "rate_per_sqft_label": result.get("rate_per_sqft_label") or f"₹{result.get('rate_per_sqft', 0):,} / sq.ft",
        "estimated_rent_monthly": result.get("estimated_rent_monthly"),
        "estimated_rent_label": result.get("estimated_rent_label") or f"{ml.short_inr(result.get('estimated_rent_monthly', 0))}/mo",
        "ai_analysis": result.get("ai_analysis") or "",
        "calculation_breakdown": result.get("calculation_breakdown") or [],
        "ai_model": result.get("ai_model") or "Groq AI (openai/gpt-oss-120b)",
    }
