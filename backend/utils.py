"""Shared helpers for serialising Mongo documents for the UI/API."""
from __future__ import annotations

from typing import Any, Optional

from .ml import predict as ml

LISTING_LABELS = {"buy": "Buy", "rent": "Rent", "commercial": "Commercial"}
PROPERTY_TYPE_LABELS = {
    "apartment": "Apartment",
    "independent-house": "Independent House",
    "villa": "Villa",
    "builder-floor": "Builder Floor",
    "studio": "Studio",
    "pg-hostel": "PG / Hostel",
    "office": "Office Space",
    "shop": "Shop / Showroom",
    "warehouse": "Warehouse",
    "plot": "Plot / Land",
}
STATUS_LABELS = {
    "pending": "Pending review",
    "active": "Active",
    "rejected": "Rejected",
    "sold": "Sold",
    "rented": "Rented out",
}

AMENITY_OPTIONS = [
    "Lift", "Car Parking", "Power Backup", "24x7 Security", "Gym",
    "Swimming Pool", "Children's Play Area", "Clubhouse", "Garden",
    "Water Supply 24x7", "Gated Community", "CCTV", "Waste Disposal",
    "Rain Water Harvesting", "Vaastu Compliant",
]

FACING_OPTIONS = ["East", "West", "North", "South", "North-East", "North-West", "South-East", "South-West"]

FURNISHING_LABELS = {
    "furnished": "Furnished",
    "semi-furnished": "Semi-Furnished",
    "unfurnished": "Unfurnished",
}

CITY_OPTIONS = [
    "Chennai", "Coimbatore", "Madurai", "Bengaluru", "Hyderabad",
    "Mumbai", "Pune", "Delhi", "Gurugram", "Noida", "Kochi", "Trichy",
]


def serialize_user(doc: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name", ""),
        "email": doc.get("email", ""),
        "phone": doc.get("phone"),
        "about": doc.get("about", ""),
        "role": doc.get("role", "user"),
        "created_at": doc.get("created_at"),
    }


def serialize_property(doc: dict[str, Any], owner: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    if not doc:
        return {}
    listing_type = doc.get("listing_type", "buy")
    price = float(doc.get("price", 0) or 0)
    area = float(doc.get("area_sqft", 0) or 0)
    images = doc.get("images") or []
    return {
        "id": str(doc["_id"]),
        "title": doc.get("title", ""),
        "description": doc.get("description", ""),
        "listing_type": listing_type,
        "listing_label": LISTING_LABELS.get(listing_type, listing_type.title()),
        "property_type": doc.get("property_type", ""),
        "property_type_label": PROPERTY_TYPE_LABELS.get(doc.get("property_type", ""), doc.get("property_type", "")),
        "price": price,
        "price_label": ml.price_label(price, listing_type),
        "price_full": ml.format_inr(price),
        "area_sqft": area,
        "price_per_sqft": round(price / area, 2) if area else 0,
        "bedrooms": doc.get("bedrooms", 0),
        "bathrooms": doc.get("bathrooms", 0),
        "balconies": doc.get("balconies", 0),
        "floor": doc.get("floor"),
        "total_floors": doc.get("total_floors"),
        "furnishing": doc.get("furnishing", "unfurnished"),
        "furnishing_label": FURNISHING_LABELS.get(doc.get("furnishing", ""), ""),
        "facing": doc.get("facing"),
        "age_years": doc.get("age_years"),
        "city": doc.get("city", ""),
        "locality": doc.get("locality", ""),
        "address": doc.get("address", ""),
        "pincode": doc.get("pincode"),
        "amenities": doc.get("amenities") or [],
        "images": images,
        "cover_image": images[0] if images else None,
        "contact_name": doc.get("contact_name"),
        "contact_phone": doc.get("contact_phone"),
        "status": doc.get("status", "active"),
        "status_label": STATUS_LABELS.get(doc.get("status", ""), ""),
        "featured": bool(doc.get("featured", False)),
        "verified": bool(doc.get("verified", False)),
        "views": int(doc.get("views", 0) or 0),
        "owner_id": str(doc.get("owner_id", "")),
        "owner_name": doc.get("owner_name") or (owner or {}).get("name", ""),
        "owner_email": (owner or {}).get("email", ""),
        "owner_phone": doc.get("contact_phone") or (owner or {}).get("phone", ""),
        "created_at": doc.get("created_at"),
    }


def bhk_label(bedrooms: int) -> str:
    return f"{bedrooms} BHK" if bedrooms else "N/A"
