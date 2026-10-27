"""Server-rendered page routes (Jinja2 templates)."""
from __future__ import annotations

import json

from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import database
from ..config import settings
from ..deps import optional_user, to_object_id
from ..utils import serialize_user
from ..ml import predict as ml
from ..utils import (
    AMENITY_OPTIONS, CITY_OPTIONS, FACING_OPTIONS, FURNISHING_LABELS,
    LISTING_LABELS, PROPERTY_TYPE_LABELS, serialize_property,
)

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(settings.base_dir / "templates"))

templates.env.globals.update(
    app_name=settings.app_name,
    amenity_options=AMENITY_OPTIONS,
    city_options=CITY_OPTIONS,
    facing_options=FACING_OPTIONS,
    furnishing_labels=FURNISHING_LABELS,
    listing_labels=LISTING_LABELS,
    property_type_labels=PROPERTY_TYPE_LABELS,
)
templates.env.filters["inr"] = ml.format_inr
templates.env.filters["short_inr"] = ml.short_inr
templates.env.filters["price_label"] = lambda p, t: ml.price_label(p, t)


def _asset_version() -> str:
    """Cache-buster from the newest static asset mtime so edits reload."""
    paths = [
        settings.base_dir / "static" / "css" / "style.css",
        settings.base_dir / "static" / "js" / "app.js",
    ]
    try:
        return str(int(max(p.stat().st_mtime for p in paths)))
    except OSError:
        return "1"


def _ctx(request: Request, user: Optional[dict], **extra: Any) -> dict[str, Any]:
    base = {
        "request": request,
        "current_user": serialize_user(user) if user else None,
        "app_name": settings.app_name,
        "asset_version": _asset_version(),
    }
    base.update(extra)
    return base


async def _saved_ids(user: Optional[dict]) -> set[str]:
    if not user:
        return set()
    rows = await database.saved().find({"user_id": user["_id"]}).to_list(length=500)
    return {str(r["property_id"]) for r in rows}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user: Optional[dict] = Depends(optional_user)):
    props = database.properties()
    featured = await props.find({"status": "active", "featured": True}).sort("created_at", -1).to_list(length=6)
    if len(featured) < 6:
        extra = await props.find({"status": "active"}).sort("created_at", -1).to_list(length=12)
        seen = {str(d["_id"]) for d in featured}
        featured += [d for d in extra if str(d["_id"]) not in seen][: 6 - len(featured)]

    counts = {t: await props.count_documents({"status": "active", "listing_type": t}) for t in ("buy", "rent", "commercial")}
    saved = await _saved_ids(user)
    return templates.TemplateResponse(
        request,
        "home.html",
        _ctx(request, user, featured=[serialize_property(d) for d in featured], counts=counts, saved_ids=saved),
    )


@router.get("/properties", response_class=HTMLResponse)
async def browse(
    request: Request,
    listing_type: Optional[str] = None,
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    q: Optional[str] = None,
    min_price: Optional[str] = None,
    max_price: Optional[str] = None,
    bedrooms: Optional[str] = None,
    furnishing: Optional[str] = None,
    sort: str = "newest",
    user: Optional[dict] = Depends(optional_user),
):
    from .properties import list_properties

    result = await list_properties(
        listing_type=listing_type, property_type=property_type, city=city, q=q,
        min_price=min_price, max_price=max_price, bedrooms=bedrooms,
        furnishing=furnishing, sort=sort, page=1, limit=24, featured=None, user=user,
    )
    facets = await database.properties().distinct("city", {"status": "active"})
    return templates.TemplateResponse(
        request,
        "browse.html",
        _ctx(
            request, user, items=result["items"], total=result["total"],
            cities=sorted(c for c in facets if c),
            filters={
                "listing_type": listing_type or "", "city": city or "", "property_type": property_type or "",
                "q": q or "", "min_price": min_price or "", "max_price": max_price or "",
                "bedrooms": bedrooms or "", "furnishing": furnishing or "", "sort": sort,
            },
        ),
    )


@router.get("/property/{property_id}", response_class=HTMLResponse)
async def property_detail(property_id: str, request: Request, user: Optional[dict] = Depends(optional_user)):
    doc = await database.properties().find_one({"_id": to_object_id(property_id)})
    if not doc:
        return templates.TemplateResponse(request, "not_found.html", _ctx(request, user), status_code=404)

    is_owner = bool(user and doc.get("owner_id") == user["_id"])
    is_admin = bool(user and user.get("role") == "admin")
    if doc.get("status") != "active" and not is_owner and not is_admin:
        return templates.TemplateResponse(request, "not_found.html", _ctx(request, user), status_code=404)

    if not is_owner:
        await database.properties().update_one({"_id": doc["_id"]}, {"$inc": {"views": 1}})
        doc["views"] = int(doc.get("views", 0)) + 1

    owner = await database.users().find_one({"_id": doc.get("owner_id")})
    item = serialize_property(doc, owner)
    item["is_owner"] = is_owner

    similar = await database.properties().find({
        "status": "active", "city": doc.get("city"), "_id": {"$ne": doc["_id"]},
        "listing_type": doc.get("listing_type"),
    }).limit(3).to_list(length=3)

    saved = await _saved_ids(user)
    return templates.TemplateResponse(
        request,
        "property.html",
        _ctx(request, user, p=item, similar=[serialize_property(d) for d in similar], saved_ids=saved),
    )


@router.get("/post", response_class=HTMLResponse)
async def post_page(request: Request, user: Optional[dict] = Depends(optional_user)):
    if not user:
        return RedirectResponse("/login?next=/post", status_code=303)
    return templates.TemplateResponse(
        request,
        "post.html",
        _ctx(request, user, p=None, mode="create", metrics_json=json.dumps(ml.metrics())),
    )


@router.get("/edit/{property_id}", response_class=HTMLResponse)
async def edit_page(property_id: str, request: Request, user: Optional[dict] = Depends(optional_user)):
    if not user:
        return RedirectResponse(f"/login?next=/edit/{property_id}", status_code=303)
    doc = await database.properties().find_one({"_id": to_object_id(property_id)})
    if not doc or (doc.get("owner_id") != user["_id"] and user.get("role") != "admin"):
        return templates.TemplateResponse(request, "not_found.html", _ctx(request, user), status_code=404)
    return templates.TemplateResponse(
        request,
        "post.html",
        _ctx(request, user, p=serialize_property(doc, user), mode="edit", metrics_json=json.dumps(ml.metrics())),
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: Optional[dict] = Depends(optional_user)):
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request, "login.html", _ctx(request, user, next=request.query_params.get("next", "")))


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, user: Optional[dict] = Depends(optional_user)):
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request, "signup.html", _ctx(request, user, next=request.query_params.get("next", "")))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, tab: str = "listings", user: Optional[dict] = Depends(optional_user)):
    if not user:
        return RedirectResponse("/login?next=/dashboard", status_code=303)

    props = await database.properties().find({"owner_id": user["_id"]}).sort("created_at", -1).to_list(length=200)
    listings = [serialize_property(d, user) for d in props]

    saved_rows = await database.saved().find({"user_id": user["_id"]}).sort("created_at", -1).to_list(length=200)
    saved_items = []
    for row in saved_rows:
        doc = await database.properties().find_one({"_id": row["property_id"]})
        if doc:
            saved_items.append(serialize_property(doc))

    from .enquiries import _serialize as serialize_enquiry
    received = [await serialize_enquiry(r) for r in
                await database.enquiries().find({"owner_id": user["_id"]}).sort("created_at", -1).to_list(length=200)]
    sent = [await serialize_enquiry(r) for r in
            await database.enquiries().find({"sender_id": user["_id"]}).sort("created_at", -1).to_list(length=200)]

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        _ctx(
            request, user, tab=tab, listings=listings, saved_items=saved_items,
            received=received, sent=sent,
            stats={
                "listings": len(listings),
                "active": sum(1 for l in listings if l["status"] == "active"),
                "saved": len(saved_items),
                "enquiries": len(received),
                "views": sum(l["views"] for l in listings),
            },
        ),
    )


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user: Optional[dict] = Depends(optional_user)):
    if not user:
        return RedirectResponse("/login?next=/admin", status_code=303)
    if user.get("role") != "admin":
        return templates.TemplateResponse(request, "not_found.html", _ctx(request, user), status_code=403)

    props = database.properties()
    docs = await props.find({}).sort("created_at", -1).to_list(length=300)
    user_docs = await database.users().find({}).sort("created_at", -1).to_list(length=500)
    users_list = []
    for d in user_docs:
        item = serialize_user(d)
        item["listings_count"] = await props.count_documents({"owner_id": d["_id"]})
        users_list.append(item)

    stats = {
        "total_properties": await props.count_documents({}),
        "active_properties": await props.count_documents({"status": "active"}),
        "pending_properties": await props.count_documents({"status": "pending"}),
        "total_users": await database.users().count_documents({}),
        "total_enquiries": await database.enquiries().count_documents({}),
        "total_predictions": await database.predictions().count_documents({}),
    }
    return templates.TemplateResponse(
        request,
        "admin.html",
        _ctx(request, user, items=[serialize_property(d) for d in docs], users=users_list, stats=stats),
    )


@router.get("/insights", response_class=HTMLResponse)
async def insights_page(request: Request, user: Optional[dict] = Depends(optional_user)):
    return templates.TemplateResponse(
        request,
        "insights.html",
        _ctx(request, user, metrics=ml.metrics(), available=ml.is_available()),
    )
