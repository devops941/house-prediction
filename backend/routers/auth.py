"""Auth API: signup, login, logout, current user."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status

from .. import database
from ..config import settings
from ..deps import current_user
from ..utils import serialize_user
from ..email_service import welcome_email
from ..models import LoginRequest, ProfileUpdate, SignupRequest
from ..security import COOKIE_NAME, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_MAX_AGE = settings.jwt_expire_minutes * 60


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, response: Response):
    email = payload.email.lower().strip()
    existing = await database.users().find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    doc = {
        "name": payload.name.strip(),
        "email": email,
        "phone": (payload.phone or "").strip() or None,
        "password_hash": hash_password(payload.password),
        "role": "user",
        "about": "",
        "created_at": datetime.now(timezone.utc),
    }
    result = await database.users().insert_one(doc)
    doc["_id"] = result.inserted_id

    token = create_access_token(str(result.inserted_id), "user")
    _set_cookie(response, token)
    welcome_email(doc["name"], email)
    return {"ok": True, "message": "Account created successfully.", "user": serialize_user(doc)}


@router.post("/login")
async def login(payload: LoginRequest, response: Response):
    email = payload.email.lower().strip()
    user = await database.users().find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(str(user["_id"]), user.get("role", "user"))
    _set_cookie(response, token)
    return {"ok": True, "message": "Logged in successfully.", "user": serialize_user(user)}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True, "message": "Logged out."}


@router.get("/me")
async def me(user: dict = Depends(current_user)):
    listings = await database.properties().count_documents({"owner_id": user["_id"]})
    return {"ok": True, "user": serialize_user(user), "listings_count": listings}


@router.put("/me")
async def update_me(payload: ProfileUpdate, user: dict = Depends(current_user)):
    updates = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if updates:
        await database.users().update_one({"_id": user["_id"]}, {"$set": updates})
    updated = await database.users().find_one({"_id": user["_id"]})
    return {"ok": True, "message": "Profile updated.", "user": serialize_user(updated)}
