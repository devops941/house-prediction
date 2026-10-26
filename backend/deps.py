"""Shared FastAPI dependencies: current user resolution + template helpers."""
from __future__ import annotations

from typing import Any, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, Request, status

from . import database
from .security import COOKIE_NAME, decode_token
from .utils import serialize_user


def to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid id")


async def optional_user(request: Request) -> Optional[dict[str, Any]]:
    """Return the logged-in user document, or None for guests."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        header = request.headers.get("Authorization", "")
        if header.lower().startswith("bearer "):
            token = header[7:].strip()
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    try:
        oid = ObjectId(payload["sub"])
    except (InvalidId, KeyError, TypeError):
        return None
    return await database.users().find_one({"_id": oid})


async def current_user(user: Optional[dict[str, Any]] = Depends(optional_user)) -> dict[str, Any]:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


async def admin_user(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


# ---------- Page-level auth (redirects instead of 401) ----------
async def page_user(request: Request) -> Optional[dict[str, Any]]:
    return await optional_user(request)


async def require_page_user(request: Request) -> dict[str, Any]:
    user = await optional_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, detail="/login")
    return user
