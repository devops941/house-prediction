"""Purely AI-driven property valuation engine.

Predicts real-time property market values, per sq.ft rates, and step-by-step
calculations dynamically using Anthropic Claude (Primary Priority) with
Groq (openai/gpt-oss-120b) as fallback.
No static or hardcoded city benchmark dictionaries are used.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from ..config import settings
from . import predict as ml_predict

logger = logging.getLogger("nestquest.ai_valuation")


async def _call_anthropic(payload: dict) -> Optional[dict]:
    """Call Anthropic API if configured for real-time market prediction (Priority 1)."""
    api_key = settings.anthropic_api_key.strip()
    model = settings.anthropic_model.strip() or "claude-haiku-4-5-20251001"
    if not api_key:
        return None

    city = (payload.get("city") or "Chennai").strip()
    locality = (payload.get("locality") or "").strip()
    ptype = (payload.get("property_type") or "apartment").strip()
    area = payload.get("area") or 1000
    bedrooms = payload.get("bedrooms") or 2
    bathrooms = payload.get("bathrooms") or 2
    stories = payload.get("stories") or 1
    parking = payload.get("parking") or 0
    furnishing = payload.get("furnishingstatus") or "semi-furnished"

    features = []
    if payload.get("mainroad"):
        features.append("Main road access")
    if payload.get("airconditioning"):
        features.append("Air conditioning")
    if payload.get("prefarea"):
        features.append("Preferred area / prime location")
    if payload.get("guestroom"):
        features.append("Guest room")
    if payload.get("basement"):
        features.append("Basement")
    if payload.get("hotwaterheating"):
        features.append("Hot water heating")
    features_str = ", ".join(features) if features else "Standard amenities"

    prompt = f"""You are a professional real estate valuation AI. Return ONLY a valid JSON object estimating the current real-world market value of this property in {city}:
- City: {city}, Locality: {locality if locality else 'City average / Central zone'}
- Type: {ptype}, Area: {area} sq.ft
- Configuration: {bedrooms} BHK, {bathrooms} Baths, {stories} Stories, Parking: {parking}
- Furnishing: {furnishing}
- Amenities: {features_str}

Return strictly a valid JSON object with keys:
{{
  "estimated_price": <number in INR>,
  "price_low": <number in INR>,
  "price_high": <number in INR>,
  "city_avg_rate_per_sqft": <number in INR/sqft>,
  "estimated_rent_monthly": <number in INR/month>,
  "ai_analysis": "<2-3 sentence market rationale for this city>",
  "calculation_breakdown": [
    {{"label": "Base City Valuation", "amount_inr": <number>, "note": "<explanation>"}},
    {{"label": "Built-up Area Value", "amount_inr": <number>, "note": "<explanation>"}},
    {{"label": "BHK & Layout Value", "amount_inr": <number>, "note": "<explanation>"}},
    {{"label": "Amenities & Furnishing", "amount_inr": <number>, "note": "<explanation>"}}
  ]
}}
"""

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": model,
        "max_tokens": 800,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=body)
        if resp.status_code != 200:
            logger.warning("Anthropic API error %s: %s", resp.status_code, resp.text[:300])
            raise RuntimeError(f"Anthropic API returned HTTP {resp.status_code}: {resp.text[:150]}")
        data = resp.json()
        raw_text = data["content"][0]["text"].strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        parsed = json.loads(raw_text)

        price = round(float(parsed.get("estimated_price") or 0))
        if price <= 0:
            raise ValueError("AI returned invalid estimated price <= 0")

        price_low = round(float(parsed.get("price_low") or (price * 0.92)))
        price_high = round(float(parsed.get("price_high") or (price * 1.08)))
        rate_per_sqft = round(float(parsed.get("city_avg_rate_per_sqft") or (price / (area or 1))))
        monthly_rent = round(float(parsed.get("estimated_rent_monthly") or ((price * 0.032) / 12)))

        raw_breakdown = parsed.get("calculation_breakdown") or []
        breakdown = []
        for item in raw_breakdown:
            amt = float(item.get("amount_inr") or 0)
            breakdown.append({
                "label": item.get("label", "Valuation Factor"),
                "amount_inr": round(amt),
                "amount_label": ml_predict.format_inr(amt),
                "note": item.get("note", ""),
            })

        return {
            "price": price,
            "price_low": price_low,
            "price_high": price_high,
            "city": city,
            "locality": locality,
            "rate_per_sqft": rate_per_sqft,
            "rate_per_sqft_label": f"₹{rate_per_sqft:,} / sq.ft",
            "estimated_rent_monthly": monthly_rent,
            "estimated_rent_label": f"{ml_predict.short_inr(monthly_rent)}/mo",
            "ai_analysis": parsed.get("ai_analysis") or f"Current market valuation for {city}.",
            "calculation_breakdown": breakdown,
            "ai_model": f"Anthropic Claude ({model})",
        }


async def _call_groq(payload: dict) -> Optional[dict]:
    """Call Groq API using the configured AI model for real-time market prediction (Fallback / Priority 2)."""
    api_key = settings.groq_api_key.strip()
    model = settings.groq_model.strip() or "openai/gpt-oss-120b"
    if not api_key:
        return None

    city = (payload.get("city") or "Chennai").strip()
    locality = (payload.get("locality") or "").strip()
    ptype = (payload.get("property_type") or "apartment").strip()
    area = payload.get("area") or 1000
    bedrooms = payload.get("bedrooms") or 2
    bathrooms = payload.get("bathrooms") or 2
    stories = payload.get("stories") or 1
    parking = payload.get("parking") or 0
    furnishing = payload.get("furnishingstatus") or "semi-furnished"

    features = []
    if payload.get("mainroad"):
        features.append("Main road access")
    if payload.get("airconditioning"):
        features.append("Air conditioning")
    if payload.get("prefarea"):
        features.append("Preferred area / prime location")
    if payload.get("guestroom"):
        features.append("Guest room")
    if payload.get("basement"):
        features.append("Basement")
    if payload.get("hotwaterheating"):
        features.append("Hot water heating")
    features_str = ", ".join(features) if features else "Standard amenities"

    prompt = f"""You are a professional real estate valuer and AI pricing engine.
Analyze the current real-world property market for the specified city and calculate an accurate valuation:

PROPERTY SPECIFICATIONS:
- City: {city}
- Locality / Landmark: {locality if locality else 'City average / Central zone'}
- Property Type: {ptype}
- Built-up Area: {area} sq.ft
- Configuration: {bedrooms} BHK, {bathrooms} Bathrooms, {stories} Stories
- Parking: {parking} space(s)
- Furnishing: {furnishing}
- Special Features & Amenities: {features_str}

YOUR TASK:
1. Dynamically analyze current real-world property market prices in {city} (and {locality} if provided).
2. Calculate the current average rate per sq.ft for this property in {city}.
3. Calculate the total fair market price in INR (integer).
4. Compute realistic price range boundaries (low and high, typically +/- 7% to 9%).
5. Calculate the estimated realistic monthly rental income in INR for this property.
6. Provide an itemized 4-step calculation breakdown showing how the total amount was calculated (Base City/Location Valuation, Built-up Area Structure, BHK & Configuration Value, Amenities & Furnishing Value).
7. Provide a concise 2-3 sentence market analysis explaining current real estate trends and valuation drivers in {city}.

Return ONLY a valid JSON object matching this schema:
{{
  "estimated_price": <total price as integer in INR>,
  "price_low": <low estimate as integer in INR>,
  "price_high": <high estimate as integer in INR>,
  "city_avg_rate_per_sqft": <rate per sqft as integer in INR>,
  "estimated_rent_monthly": <monthly rent as integer in INR>,
  "ai_analysis": "<2-3 sentence market rationale for this city>",
  "calculation_breakdown": [
    {{"label": "Base City Valuation", "amount_inr": <number>, "note": "<explanation with current rate>"}},
    {{"label": "Built-up Area Value", "amount_inr": <number>, "note": "<explanation>"}},
    {{"label": "BHK & Layout Value", "amount_inr": <number>, "note": "<explanation>"}},
    {{"label": "Amenities & Furnishing", "amount_inr": <number>, "note": "<explanation>"}}
  ]
}}
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a professional real-estate valuation AI. You analyze cities dynamically and return strictly valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
        if resp.status_code != 200:
            logger.error("Groq AI API error %s: %s", resp.status_code, resp.text[:300])
            raise RuntimeError(f"Groq API returned HTTP {resp.status_code}: {resp.text[:150]}")
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        price = round(float(parsed.get("estimated_price") or 0))
        if price <= 0:
            raise ValueError("AI returned invalid estimated price <= 0")

        price_low = round(float(parsed.get("price_low") or (price * 0.92)))
        price_high = round(float(parsed.get("price_high") or (price * 1.08)))
        rate_per_sqft = round(float(parsed.get("city_avg_rate_per_sqft") or (price / (area or 1))))
        monthly_rent = round(float(parsed.get("estimated_rent_monthly") or ((price * 0.032) / 12)))

        raw_breakdown = parsed.get("calculation_breakdown") or []
        breakdown = []
        for item in raw_breakdown:
            amt = float(item.get("amount_inr") or 0)
            breakdown.append({
                "label": item.get("label", "Valuation Factor"),
                "amount_inr": round(amt),
                "amount_label": ml_predict.format_inr(amt),
                "note": item.get("note", ""),
            })

        return {
            "price": price,
            "price_low": price_low,
            "price_high": price_high,
            "city": city,
            "locality": locality,
            "rate_per_sqft": rate_per_sqft,
            "rate_per_sqft_label": f"₹{rate_per_sqft:,} / sq.ft",
            "estimated_rent_monthly": monthly_rent,
            "estimated_rent_label": f"{ml_predict.short_inr(monthly_rent)}/mo",
            "ai_analysis": parsed.get("ai_analysis") or f"Current market valuation for {city}.",
            "calculation_breakdown": breakdown,
            "ai_model": f"Groq AI ({model})",
        }


async def estimate_property_value(payload: dict) -> dict:
    """Predict accurate property market value purely using AI models.

    Execution Order:
      1. Anthropic Claude (Primary Priority)
      2. Groq AI (Automatic Fallback if Anthropic fails or lacks credits)
    """
    last_error: Optional[Exception] = None

    # Priority 1: Try Anthropic Claude
    if settings.anthropic_api_key:
        try:
            logger.info("Priority 1: Attempting property valuation with Anthropic (%s)...", settings.anthropic_model)
            res = await _call_anthropic(payload)
            if res:
                return res
        except Exception as exc:
            logger.warning("Anthropic Claude failed (%s). Falling back to Groq AI...", exc)
            last_error = exc

    # Priority 2: Fallback to Groq AI (openai/gpt-oss-120b)
    if settings.groq_api_key:
        try:
            logger.info("Priority 2: Attempting property valuation with Groq AI (%s)...", settings.groq_model)
            res = await _call_groq(payload)
            if res:
                return res
        except Exception as exc:
            logger.warning("Groq AI prediction attempt failed: %s", exc)
            last_error = exc

    # If neither succeeded, raise an error explaining the issue
    error_msg = f"AI valuation failed: {last_error}" if last_error else "No AI API key configured in .env"
    raise RuntimeError(error_msg)
