"""Properties API: create, list/search, detail, update, delete, save, view."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .. import database
from ..deps import admin_user, current_user, optional_user, to_object_id
from ..models import PropertyCreate, PropertyUpdate, StatusUpdate
from ..utils import serialize_property

router = APIRouter(prefix="/api/properties", tags=["properties"])

SORT_FIELDS = {
    "newest": [("created_at", -1)],
    "price_asc": [("price", 1)],
    "price_desc": [("price", -1)],
    "area_desc": [("area_sqft", -1)],
    "popular": [("views", -1)],
}


def _sort(sort: str):
    return SORT_FIELDS.get(sort, SORT_FIELDS["newest"])


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value in (None, "", "any"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def _attach_owner(doc: dict[str, Any]) -> dict[str, Any]:
    owner = await database.users().find_one({"_id": doc.get("owner_id")})
    return serialize_property(doc, owner)


@router.get("")
async def list_properties(
    listing_type: Optional[str] = None,
    property_type: Optional[str] = None,
    city: Optional[str] = None,
    locality: Optional[str] = None,
    q: Optional[str] = None,
    min_price: Optional[str] = None,
    max_price: Optional[str] = None,
    bedrooms: Optional[str] = None,
    furnishing: Optional[str] = None,
    min_area: Optional[str] = None,
    max_area: Optional[str] = None,
    sort: str = "newest",
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=60),
    featured: Optional[bool] = None,
    user: Optional[dict] = Depends(optional_user),
):
    query: dict[str, Any] = {"status": "active"}

    if listing_type in ("buy", "rent", "commercial"):
        query["listing_type"] = listing_type
    if property_type:
        query["property_type"] = property_type
    if city:
        query["city"] = {"$regex": f"^{city.strip()}$", "$options": "i"}
    if locality:
        query["locality"] = {"$regex": locality.strip(), "$options": "i"}
    if furnishing:
        query["furnishing"] = furnishing
    if featured:
        query["featured"] = True

    if q:
        query["$or"] = [
            {"title": {"$regex": q.strip(), "$options": "i"}},
            {"description": {"$regex": q.strip(), "$options": "i"}},
            {"locality": {"$regex": q.strip(), "$options": "i"}},
            {"city": {"$regex": q.strip(), "$options": "i"}},
        ]

    lo, hi = _parse_float(min_price), _parse_float(max_price)
    if lo is not None or hi is not None:
        price_filter: dict[str, float] = {}
        if lo is not None:
            price_filter["$gte"] = lo
        if hi is not None:
            price_filter["$lte"] = hi
        query["price"] = price_filter

    area_lo, area_hi = _parse_float(min_area), _parse_float(max_area)
    if area_lo is not None or area_hi is not None:
        area_filter: dict[str, float] = {}
        if area_lo is not None:
            area_filter["$gte"] = area_lo
        if area_hi is not None:
            area_filter["$lte"] = area_hi
        query["area_sqft"] = area_filter

    bhk = _parse_float(bedrooms)
    if bhk is not None:
        query["bedrooms"] = {"$gte": int(bhk)}

    total = await database.properties().count_documents(query)
    cursor = (
        database.properties()
        .find(query)
        .sort(_sort(sort))
        .skip((page - 1) * limit)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)

    saved_ids: set[str] = set()
    if user:
        rows = await database.saved().find({"user_id": user["_id"]}).to_list(length=500)
        saved_ids = {str(r["property_id"]) for r in rows}

    items = []
    for doc in docs:
        item = await _attach_owner(doc)
        item["is_saved"] = item["id"] in saved_ids
        item["is_owner"] = bool(user and doc.get("owner_id") == user["_id"])
        items.append(item)

    return {
        "ok": True,
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, math.ceil(total / limit)),
    }


@router.get("/facets")
async def facets():
    """Distinct values for building filter dropdowns."""
    cities = await database.properties().distinct("city", {"status": "active"})
    types = await database.properties().distinct("property_type", {"status": "active"})
    return {"ok": True, "cities": sorted(c for c in cities if c), "property_types": sorted(t for t in types if t)}


@router.get("/my")
async def my_properties(user: dict = Depends(current_user)):
    docs = await database.properties().find({"owner_id": user["_id"]}).sort("created_at", -1).to_list(length=200)
    items = [serialize_property(d, user) for d in docs]
    return {"ok": True, "items": items, "total": len(items)}


@router.get("/saved")
async def saved_properties(user: dict = Depends(current_user)):
    rows = await database.saved().find({"user_id": user["_id"]}).sort("created_at", -1).to_list(length=200)
    items = []
    for row in rows:
        doc = await database.properties().find_one({"_id": row["property_id"]})
        if doc:
            item = await _attach_owner(doc)
            item["is_saved"] = True
            items.append(item)
    return {"ok": True, "items": items, "total": len(items)}


@router.get("/{property_id}")
async def get_property(property_id: str, user: Optional[dict] = Depends(optional_user)):
    oid = to_object_id(property_id)
    doc = await database.properties().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Property not found.")

    is_owner = bool(user and doc.get("owner_id") == user["_id"])
    is_admin = bool(user and user.get("role") == "admin")
    if doc.get("status") != "active" and not is_owner and not is_admin:
        raise HTTPException(status_code=404, detail="Property not found.")

    if not is_owner:
        await database.properties().update_one({"_id": oid}, {"$inc": {"views": 1}})
        doc["views"] = int(doc.get("views", 0)) + 1

    item = await _attach_owner(doc)
    item["is_owner"] = is_owner
    if user:
        item["is_saved"] = bool(await database.saved().find_one({"user_id": user["_id"], "property_id": oid}))
    return {"ok": True, "property": item}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_property(payload: PropertyCreate, user: dict = Depends(current_user)):
    data = payload.model_dump()
    data.update({
        "owner_id": user["_id"],
        "owner_name": user.get("name", ""),
        "status": "active",
        "featured": False,
        "verified": False,
        "views": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })
    result = await database.properties().insert_one(data)
    data["_id"] = result.inserted_id
    return {"ok": True, "message": "Property posted successfully.", "property": await _attach_owner(data)}


@router.put("/{property_id}")
async def update_property(property_id: str, payload: PropertyUpdate, user: dict = Depends(current_user)):
    oid = to_object_id(property_id)
    doc = await database.properties().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Property not found.")
    if doc.get("owner_id") != user["_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="You can only edit your own listings.")

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update.")
    updates["updated_at"] = datetime.now(timezone.utc)
    await database.properties().update_one({"_id": oid}, {"$set": updates})
    doc = await database.properties().find_one({"_id": oid})
    return {"ok": True, "message": "Listing updated.", "property": await _attach_owner(doc)}


@router.delete("/{property_id}")
async def delete_property(property_id: str, user: dict = Depends(current_user)):
    oid = to_object_id(property_id)
    doc = await database.properties().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Property not found.")
    if doc.get("owner_id") != user["_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="You can only delete your own listings.")

    await database.properties().delete_one({"_id": oid})
    await database.saved().delete_many({"property_id": oid})
    await database.enquiries().delete_many({"property_id": oid})
    return {"ok": True, "message": "Listing deleted."}


@router.post("/{property_id}/save")
async def toggle_save(property_id: str, user: dict = Depends(current_user)):
    oid = to_object_id(property_id)
    doc = await database.properties().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Property not found.")

    existing = await database.saved().find_one({"user_id": user["_id"], "property_id": oid})
    if existing:
        await database.saved().delete_one({"_id": existing["_id"]})
        return {"ok": True, "saved": False, "message": "Removed from shortlist."}

    await database.saved().insert_one({
        "user_id": user["_id"],
        "property_id": oid,
        "created_at": datetime.now(timezone.utc),
    })
    return {"ok": True, "saved": True, "message": "Added to shortlist."}


@router.patch("/{property_id}/status")
async def set_status(property_id: str, payload: StatusUpdate, admin: dict = Depends(admin_user)):
    oid = to_object_id(property_id)
    doc = await database.properties().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Property not found.")

    updates: dict[str, Any] = {"status": payload.status, "updated_at": datetime.now(timezone.utc)}
    if payload.featured is not None:
        updates["featured"] = payload.featured
    if payload.status == "active":
        updates["verified"] = True
    await database.properties().update_one({"_id": oid}, {"$set": updates})
    doc = await database.properties().find_one({"_id": oid})
    return {"ok": True, "message": f"Listing marked as {payload.status}.", "property": serialize_property(doc)}
