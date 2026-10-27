"""Cloudinary integration for NestQuest image uploads."""
from __future__ import annotations

import logging
from functools import lru_cache

import cloudinary
import cloudinary.uploader

from .config import settings

logger = logging.getLogger("nestquest.cloudinary")


def is_enabled() -> bool:
    """Return True only if all three Cloudinary settings are non-empty."""
    return bool(
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    )


@lru_cache
def _configure() -> bool:
    """Configure the Cloudinary SDK once; return True on success."""
    if not is_enabled():
        return False
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    return True


def upload_image(data: bytes, filename: str | None = None) -> str:
    """Upload raw image bytes to Cloudinary and return the secure URL.

    Raises RuntimeError if Cloudinary is not configured.
    Any upload exception is propagated to the caller.
    """
    if not _configure():
        raise RuntimeError("Cloudinary is not configured")
    result = cloudinary.uploader.upload(data, folder="nestquest", resource_type="image")
    return result["secure_url"]
