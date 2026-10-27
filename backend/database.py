"""MongoDB (Motor) connection, index management and collection accessors."""
from __future__ import annotations

import logging
from typing import Optional

import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


def connect() -> AsyncIOMotorDatabase:
    """Create the shared Motor client (idempotent)."""
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(
            settings.database_url,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=15000,
            uuidRepresentation="standard",
        )
        _db = _client[settings.db_name]
    return _db


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        return connect()
    return _db


def close() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


# ---- Collection accessors -------------------------------------------------
def users():
    return get_db()["users"]


def properties():
    return get_db()["properties"]


def enquiries():
    return get_db()["enquiries"]


def saved():
    return get_db()["saved"]


def predictions():
    return get_db()["predictions"]


async def ping() -> bool:
    try:
        await get_db().command("ping")
        return True
    except Exception as exc:  # pragma: no cover - connectivity guard
        logger.error("MongoDB ping failed: %s", exc)
        return False


async def ensure_indexes() -> None:
    """Create the indexes the app relies on. Safe to call on every boot."""
    await users().create_index("email", unique=True)
    await properties().create_index([("city", 1), ("listing_type", 1), ("status", 1)])
    await properties().create_index([("owner_id", 1)])
    await properties().create_index([("created_at", -1)])
    await properties().create_index([("price", 1)])
    await properties().create_index([("property_type", 1)])
    await properties().create_index(
        [("title", "text"), ("description", "text"), ("locality", "text"), ("city", "text")],
        name="property_text_search",
    )
    await saved().create_index([("user_id", 1), ("property_id", 1)], unique=True)
    await enquiries().create_index([("owner_id", 1), ("created_at", -1)])
    await enquiries().create_index([("sender_id", 1), ("created_at", -1)])
    await predictions().create_index([("created_at", -1)])
    logger.info("MongoDB indexes ensured")
