"""Admin API: dashboard stats, user management, listing moderation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from .. import database
from ..deps import admin_user, to_object_id
from ..utils import serialize_property, serialize_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
async def stats(admin: dict = Depends(admin_user)):
    props = database.properties()
    users = database.users()
    now = datetime.now(timezone.utc)

    by_listing = {
        t: await props.count_documents({"listing_type": t})
        for t in ("buy", "rent", "commercial")
    }
    recent = await props.count_documents({"created_at": {"$gte": now - timedelta(days=7)}})
    return {
        "ok": True,
        "stats": {
            "total_properties": await props.count_documents({}),
            "active_properties": await props.count_documents({"status": "active"}),
            "pending_properties": await props.count_documents({"status": "pending"}),
            "total_users": await users.count_documents({}),
            "total_enquiries": await database.enquiries().count_documents({}),
            "total_predictions": await database.predictions().count_documents({}),
            "new_this_week": recent,
            "by_listing_type": by_listing,
        },
    }


@router.get("/properties")
async def all_properties(status: str | None = None, admin: dict = Depends(admin_user)):
    query = {"status": status} if status else {}
    docs = await database.properties().find(query).sort("created_at", -1).to_list(length=500)
    return {"ok": True, "items": [serialize_property(d) for d in docs], "total": len(docs)}


@router.get("/users")
async def all_users(admin: dict = Depends(admin_user)):
    docs = await database.users().find({}).sort("created_at", -1).to_list(length=1000)
    items = []
    for doc in docs:
        item = serialize_user(doc)
        item["listings_count"] = await database.properties().count_documents({"owner_id": doc["_id"]})
        items.append(item)
    return {"ok": True, "items": items, "total": len(items)}


@router.patch("/users/{user_id}/role")
async def set_role(user_id: str, role: str, admin: dict = Depends(admin_user)):
    if role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'.")
    oid = to_object_id(user_id)
    if oid == admin["_id"]:
        raise HTTPException(status_code=400, detail="You cannot change your own role.")
    result = await database.users().update_one({"_id": oid}, {"$set": {"role": role}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"ok": True, "message": f"User role set to {role}."}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(admin_user)):
    oid = to_object_id(user_id)
    if oid == admin["_id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
    result = await database.users().delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")
    await database.properties().delete_many({"owner_id": oid})
    await database.saved().delete_many({"user_id": oid})
    return {"ok": True, "message": "User and their listings removed."}
