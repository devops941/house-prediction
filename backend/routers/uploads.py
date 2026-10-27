"""Uploads router: server-side image upload to Cloudinary."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from ..deps import current_user
from .. import cloudinary_service

logger = logging.getLogger("nestquest.uploads")

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

MAX_FILES = 15
MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@router.get("/status")
async def upload_status():
    """Return whether Cloudinary image upload is configured."""
    return {"ok": True, "enabled": cloudinary_service.is_enabled()}


@router.post("/images")
async def upload_images(
    files: list[UploadFile] = File(...),
    user: dict = Depends(current_user),
):
    """Upload one or more image files to Cloudinary and return their URLs."""
    if not cloudinary_service.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image upload is not configured.",
        )

    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")

    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload at most {MAX_FILES} images at once.",
        )

    urls: list[str] = []

    for file in files:
        if not (file.content_type or "").startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{file.filename}: only image files are allowed.",
            )

        data = await file.read()

        if len(data) > MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{file.filename}: image exceeds 10 MB.",
            )

        if not data:
            continue

        try:
            url = await run_in_threadpool(cloudinary_service.upload_image, data, file.filename)
            urls.append(url)
        except Exception:
            logger.exception("Cloudinary upload failed for file %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Image upload failed. Please try again.",
            )

    return {"ok": True, "urls": urls, "message": f"{len(urls)} image(s) uploaded."}
