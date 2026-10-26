"""FastAPI application entrypoint for NestQuest."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import database
from .config import settings
from .ml import predict as ml_engine
from .routers import admin, auth, enquiries, pages, properties
from .routers import ml as ml_router
from .seed import seed_admin, seed_demo_properties

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nestquest")


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.connect()
    if await database.ping():
        logger.info("Connected to MongoDB database '%s'", settings.db_name)
        await database.ensure_indexes()
        await seed_admin()
        await seed_demo_properties()
    else:
        logger.error("Could not reach MongoDB -- API calls that touch the DB will fail.")
    yield
    database.close()


app = FastAPI(title=f"{settings.app_name} API", version="1.0.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(settings.base_dir / "static")), name="static")

app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(enquiries.router)
app.include_router(admin.router)
app.include_router(ml_router.router)
app.include_router(pages.router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    wants_json = request.url.path.startswith("/api/") or "application/json" in request.headers.get("accept", "")
    if wants_json:
        return JSONResponse(status_code=exc.status_code, content={"ok": False, "detail": exc.detail})
    if exc.status_code in (301, 302, 303, 307, 308) and isinstance(exc.detail, str) and exc.detail.startswith("/"):
        from fastapi.responses import RedirectResponse

        return RedirectResponse(exc.detail, status_code=303)
    if exc.status_code == 401:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(f"/login?next={request.url.path}", status_code=303)
    if exc.status_code == 403:
        return JSONResponse(status_code=403, content={"ok": False, "detail": exc.detail})
    return JSONResponse(status_code=exc.status_code, content={"ok": False, "detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    loc = ".".join(str(p) for p in first.get("loc", []) if p not in ("body", "query"))
    msg = first.get("msg", "Invalid input")
    detail = f"{loc}: {msg}" if loc else msg
    return JSONResponse(status_code=422, content={"ok": False, "detail": detail, "errors": exc.errors()})


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "app": settings.app_name,
        "database": await database.ping(),
        "model_available": ml_engine.is_available(),
    }
