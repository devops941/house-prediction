"""Wraps the existing scikit-learn model as an AI price-estimate service."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from ..config import settings

MODEL_PATH = settings.base_dir / "model" / "model.pkl"
COLUMNS_PATH = settings.base_dir / "model" / "columns.pkl"
METRICS_PATH = settings.base_dir / "model" / "metrics.json"


@lru_cache
def _load_model():
    if not MODEL_PATH.exists() or not COLUMNS_PATH.exists():
        return None, None
    return joblib.load(MODEL_PATH), joblib.load(COLUMNS_PATH)


@lru_cache
def _load_metrics() -> dict:
    if not METRICS_PATH.exists():
        return {}
    try:
        return json.loads(METRICS_PATH.read_text())
    except json.JSONDecodeError:
        return {}


def metrics() -> dict:
    return _load_metrics()


def is_available() -> bool:
    model, columns = _load_model()
    return model is not None and columns is not None


def estimate(payload: dict) -> dict:
    """Return {price, price_low, price_high, rmse} for the given features."""
    model, columns = _load_model()
    if model is None:
        raise RuntimeError("Model artefacts are missing; cannot estimate price.")

    row = {
        "area": payload["area"],
        "bedrooms": payload["bedrooms"],
        "bathrooms": payload["bathrooms"],
        "stories": payload["stories"],
        "mainroad": 1 if payload["mainroad"] else 0,
        "guestroom": 1 if payload["guestroom"] else 0,
        "basement": 1 if payload["basement"] else 0,
        "hotwaterheating": 1 if payload["hotwaterheating"] else 0,
        "airconditioning": 1 if payload["airconditioning"] else 0,
        "parking": payload["parking"],
        "prefarea": 1 if payload["prefarea"] else 0,
        "furnishingstatus_semi-furnished": 1 if payload["furnishingstatus"] == "semi-furnished" else 0,
        "furnishingstatus_unfurnished": 1 if payload["furnishingstatus"] == "unfurnished" else 0,
    }
    frame = pd.DataFrame([row]).reindex(columns=columns, fill_value=0)
    price = max(float(model.predict(frame)[0]), 0.0)

    rmse = float(_load_metrics().get("linear_regression", {}).get("rmse", 0) or 0)
    spread = max(price * 0.08, rmse)
    return {
        "price": round(price, 2),
        "price_low": round(max(price - spread, 0.0), 2),
        "price_high": round(price + spread, 2),
        "rmse": round(rmse, 2),
    }


def format_inr(amount: float) -> str:
    amount = int(round(amount))
    sign = "-" if amount < 0 else ""
    digits = str(abs(amount))
    if len(digits) > 3:
        last3, rest, groups = digits[-3:], digits[:-3], []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        digits = ",".join(groups) + "," + last3
    return f"{sign}\u20b9{digits}"


def short_inr(amount: float) -> str:
    amount = abs(float(amount))
    if amount >= 1_00_00_000:
        return f"\u20b9{amount / 1_00_00_000:.2f} Cr"
    if amount >= 1_00_000:
        return f"\u20b9{amount / 1_00_000:.2f} L"
    if amount >= 1_000:
        return f"\u20b9{amount / 1_000:.0f}K"
    return f"\u20b9{amount:.0f}"


def price_label(price: float, listing_type: str) -> str:
    return f"{short_inr(price)}/mo" if listing_type == "rent" else short_inr(price)
