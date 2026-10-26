"""Enquiries API: send, receive, reply."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from .. import database
from ..deps import current_user, optional_user, to_object_id
from ..utils import serialize_user
from ..email_service import enquiry_email
from ..models import EnquiryCreate, EnquiryReply

router = APIRouter(prefix="/api/enquiries", tags=["enquiries"])


async def _serialize(enquiry: dict[str, Any], *, include_property: bool = True) -> dict[str, Any]:
    out = {
        "id": str(enquiry["_id"]),
        "message": enquiry.get("message", ""),
        "phone": enquiry.get("phone"),
        "reply": enquiry.get("reply"),
        "status": enquiry.get("status", "open"),
        "created_at": enquiry.get("created_at"),
        "property_id": str(enquiry.get("property_id", "")),
        "sender_id": str(enquiry.get("sender_id", "")),
        "sender_name": enquiry.get("sender_name", ""),
        "sender_email": enquiry.get("sender_email", ""),
    }
    if include_property:
        prop = await database.properties().find_one({"_id": enquiry.get("property_id")})
        out["property_title"] = prop.get("title", "Listing removed") if prop else "Listing removed"
        out["property_city"] = prop.get("city", "") if prop else ""
        out["property_price_label"] = prop.get("price", 0) if prop else 0
    return out


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_enquiry(payload: EnquiryCreate, user: Optional[dict] = Depends(optional_user)):
    oid = to_object_id(payload.property_id)
    prop = await database.properties().find_one({"_id": oid})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found.")

    if user and prop.get("owner_id") == user["_id"]:
        raise HTTPException(status_code=400, detail="You cannot enquire about your own listing.")

    sender_name = user.get("name") if user else "Guest"
    sender_email = user.get("email") if user else ""
    sender_id = user["_id"] if user else None

    doc = {
        "property_id": oid,
        "owner_id": prop.get("owner_id"),
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "message": payload.message.strip(),
        "phone": (payload.phone or (user.get("phone") if user else "") or "").strip() or None,
        "reply": None,
        "status": "open",
        "created_at": datetime.now(timezone.utc),
    }
    result = await database.enquiries().insert_one(doc)
    doc["_id"] = result.inserted_id

    owner = await database.users().find_one({"_id": prop.get("owner_id")})
    if owner:
        enquiry_email(
            owner.get("name", "Owner"),
            owner.get("email", ""),
            prop.get("title", "your listing"),
            sender_name,
            doc["message"],
            doc["phone"] or "",
        )

    return {"ok": True, "message": "Enquiry sent to the owner.", "enquiry": await _serialize(doc)}


@router.get("/received")
async def received(user: dict = Depends(current_user)):
    rows = await database.enquiries().find({"owner_id": user["_id"]}).sort("created_at", -1).to_list(length=300)
    items = [await _serialize(r) for r in rows]
    return {"ok": True, "items": items, "total": len(items)}


@router.get("/sent")
async def sent(user: dict = Depends(current_user)):
    rows = await database.enquiries().find({"sender_id": user["_id"]}).sort("created_at", -1).to_list(length=300)
    items = [await _serialize(r) for r in rows]
    return {"ok": True, "items": items, "total": len(items)}


@router.post("/{enquiry_id}/reply")
async def reply(enquiry_id: str, payload: EnquiryReply, user: dict = Depends(current_user)):
    oid = to_object_id(enquiry_id)
    enquiry = await database.enquiries().find_one({"_id": oid})
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found.")
    if enquiry.get("owner_id") != user["_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only the listing owner can reply.")

    await database.enquiries().update_one(
        {"_id": oid},
        {"$set": {"reply": payload.reply.strip(), "status": "replied", "replied_at": datetime.now(timezone.utc)}},
    )
    enquiry = await database.enquiries().find_one({"_id": oid})
    return {"ok": True, "message": "Reply sent.", "enquiry": await _serialize(enquiry)}
