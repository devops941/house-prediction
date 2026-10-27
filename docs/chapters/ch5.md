# 5. IMPLEMENTATION

## 5.1 Computing Environment Setup

The NestQuest platform is implemented in Python 3.12 and requires only an isolated virtual environment and the packages listed in `requirements.txt`. The commands below show the canonical setup procedure for a Windows development machine.

```bash
# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install all runtime and development dependencies
pip install -r requirements.txt

# Copy the sample environment file and populate secrets
copy .env.example .env

# Start the development server (http://localhost:8000)
python run.py
```

The `run.py` entry point calls `uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)`. During the lifespan startup sequence, the Motor client connects to MongoDB Atlas, idempotent indexes are created, and the admin account and optional demo data are seeded before the first HTTP request is accepted. No build step or bundler is required; Jinja2 templates are rendered server-side and static files are served with a cache-buster query string.

## 5.2 Project Structure

The repository separates the Python backend package, server-rendered templates, static assets, ML artefacts, and the training notebook.

```text
house_price_prediction/
├── backend/
│   ├── main.py          # App factory, lifespan, exception handlers, /api/health
│   ├── config.py        # .env loader + Settings singleton (lru_cache)
│   ├── database.py      # Motor client, collection accessors, ensure_indexes()
│   ├── security.py      # bcrypt hash/verify, JWT create/decode, COOKIE_NAME
│   ├── models.py        # Pydantic v2 schemas (SignupRequest, PropertyCreate, …)
│   ├── deps.py          # optional_user → current_user → admin_user, page_user
│   ├── utils.py         # serialize_user, serialize_property, option lists
│   ├── seed.py          # admin + 20 demo listings
│   ├── email_service.py # Optional SMTP (disabled by default)
│   ├── cloudinary_service.py  # Cloudinary config + upload_image()
│   ├── ml/
│   │   └── predict.py   # AI price estimator (joblib load, lru_cache)
│   └── routers/
│       ├── auth.py      # /api/auth — signup, login, logout, me
│       ├── properties.py# /api/properties — CRUD, search, shortlist
│       ├── enquiries.py # /api/enquiries — send, receive, reply
│       ├── admin.py     # /api/admin — stats, moderation, user management
│       ├── ml.py        # /api/ml — predict, status
│       ├── uploads.py   # /api/uploads — Cloudinary image upload
│       └── pages.py     # Server-rendered HTML page routes
├── templates/
│   ├── base.html        # Shared layout (nav, toast, footer)
│   ├── index.html, properties.html, post.html, …
│   └── _card.html       # Property card macro
├── static/
│   ├── css/style.css    # ~460 lines, hand-written CSS
│   └── js/app.js        # ~450 lines, fetch wrapper API + page initialisers
├── model/
│   ├── model.pkl        # Trained LinearRegression (joblib)
│   ├── columns.pkl      # 13 feature column names
│   └── metrics.json     # R², MAE, RMSE for both models
├── data/Housing.csv     # 545-row synthetic dataset
├── notebook/house_price_training.ipynb
├── requirements.txt
├── run.py
└── .env                 # (not committed; secrets loaded at runtime)
```

Each router carries its own URL prefix, keeping routing concerns localised and making it straightforward to expand or replace individual subsystems.

[[TABLE Table 5.1 — Key Python dependencies.]]
| Package | Version constraint | Purpose |
|---|---|---|
| fastapi | >=0.115 | ASGI web framework, routing, dependency injection |
| uvicorn[standard] | >=0.32 | ASGI server (HTTP/1.1 + WebSocket; includes uvloop on Linux) |
| jinja2 | >=3.1 | Server-side HTML templating |
| python-multipart | >=0.0.12 | Multipart form / file upload parsing |
| motor | >=3.6 | Async MongoDB driver (wraps pymongo with asyncio) |
| pymongo | >=4.9 | Underlying MongoDB client; also used for BSON ObjectId |
| certifi | >=2024.8 | CA bundle for TLS connection to MongoDB Atlas |
| bcrypt | >=4.2 | Password hashing (cost factor 12) |
| PyJWT | >=2.9 | JSON Web Token creation and verification (HS256) |
| email-validator | >=2.2 | Pydantic email field validation |
| pandas | >=2.0 | DataFrame construction for ML inference |
| numpy | >=1.26 | Numerical operations; random seed in dataset generation |
| scikit-learn | >=1.4 | LinearRegression model, joblib-serialised artefact |
| joblib | >=1.3 | Model and columns serialisation / deserialisation |
| matplotlib | >=3.7 | EDA chart generation in the training notebook |
| seaborn | >=0.12 | Statistical visualisations (heatmap, KDE) |
| cloudinary | >=1.40 | Server-side image upload to Cloudinary CDN |

Each package has a minimum-version pin to ensure reproducible installs. The `uvicorn[standard]` extra pulls in `httptools` and `uvloop` (on Linux) for higher throughput than the pure-Python fallbacks.

[[TABLE Table 5.2 — Environment variable keys (values are deployment secrets — not shown).]]
| Variable | Description |
|---|---|
| `DATABASE_URL` | MongoDB Atlas connection string (mongodb+srv://…) |
| `DB_NAME` | Target database name within the Atlas cluster |
| `JWT_SECRET` | HMAC-HS256 signing key for JSON Web Tokens |
| `JWT_ALGORITHM` | Algorithm identifier (default: HS256) |
| `JWT_EXPIRE_MINUTES` | Token lifetime in minutes (default: 10080 = 7 days) |
| `SMTP_HOST` | Outgoing mail server hostname |
| `SMTP_PORT` | SMTP port (default: 587) |
| `SMTP_USER` | SMTP authentication username |
| `SMTP_PASS` | SMTP authentication password |
| `SMTP_FROM` | Sender address for system emails |
| `SMTP_ENABLED` | Set to `true` to enable email delivery (default: false) |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary account cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `ADMIN_EMAIL` | Email address for the bootstrapped admin account |
| `ADMIN_PASSWORD` | Initial admin password |
| `ADMIN_NAME` | Display name for the admin account |
| `SEED_DEMO_DATA` | Set to `true` to insert demo listings on first boot |
| `APP_NAME` | Application display name (default: NestQuest) |

Secret values are never committed to version control; `.env` is listed in `.gitignore`. The `config.py` module provides safe defaults for every non-secret variable, though `DATABASE_URL` must be supplied for any MongoDB functionality.

## 5.3 Backend Implementation

The backend is a FastAPI application package under `backend/`. The following snippets present key modules with their design rationale.

**Settings loader (`backend/config.py`)**

```python
from __future__ import annotations
import os
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))

_load_dotenv(BASE_DIR / ".env")

class Settings:
    def __init__(self) -> None:
        self.jwt_secret = os.environ.get("JWT_SECRET", "dev-insecure-secret")
        self.jwt_expire_minutes = int(os.environ.get("JWT_EXPIRE_MINUTES", "10080"))
        self.database_url = os.environ.get("DATABASE_URL", "")

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Rather than introducing `python-dotenv`, the project implements a minimal loader in ~15 lines. `os.environ.setdefault` ensures shell-environment variables take precedence over the file, which is important for containerised deployments. `@lru_cache` makes the `Settings` singleton cheap to access from any module.

**Password hashing and JWT (`backend/security.py`)**

```python
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from .config import settings

COOKIE_NAME = "nestquest_token"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False

def create_access_token(subject: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject), "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
```

bcrypt cost factor 12 balances brute-force resistance against server-side latency. The JWT payload carries `sub` (MongoDB `_id`), `role`, `iat`, and `exp`; tokens are signed with HMAC-HS256 and stored in an httpOnly cookie to prevent XSS token theft. `verify_password` wraps `bcrypt.checkpw` in a try/except to guard against malformed stored hashes.

**Motor index creation (`backend/database.py`)**

```python
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
from .config import settings

async def ensure_indexes() -> None:
    db = get_db()
    await db["users"].create_index("email", unique=True)
    await db["properties"].create_index(
        [("city", 1), ("listing_type", 1), ("status", 1)]
    )
    await db["properties"].create_index(
        [("title", "text"), ("description", "text"),
         ("locality", "text"), ("city", "text")],
        name="property_text_search",
    )
    await db["saved"].create_index(
        [("user_id", 1), ("property_id", 1)], unique=True
    )
    await db["predictions"].create_index([("created_at", -1)])
```

`ensure_indexes` is called on every startup inside the `lifespan` context manager; if indexes already exist MongoDB returns silently. The compound index on `city`, `listing_type`, and `status` supports the most common browse query; the text index enables keyword search; the unique compound index on `saved` enforces the one-shortlist-per-user-per-property business rule without application-level locking.

**Login router endpoint (`backend/routers/auth.py`)**

```python
from fastapi import APIRouter, HTTPException, Response, status
from ..security import COOKIE_NAME, create_access_token, verify_password
from .. import database
from ..models import LoginRequest
from ..utils import serialize_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login")
async def login(payload: LoginRequest, response: Response):
    email = payload.email.lower().strip()
    user = await database.users().find_one({"email": email})
    if not user or not verify_password(payload.password,
                                        user.get("password_hash", "")):
        raise HTTPException(status_code=401,
                            detail="Invalid email or password.")
    token = create_access_token(str(user["_id"]), user.get("role", "user"))
    response.set_cookie(
        key=COOKIE_NAME, value=token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True, samesite="lax", secure=False, path="/",
    )
    return {"ok": True, "user": serialize_user(user)}
```

Whether the user does not exist or the password is wrong, the endpoint returns the same HTTP 401 message, preventing user-enumeration. The JWT is written into an httpOnly cookie with `samesite="lax"` for CSRF protection. `secure=False` is appropriate for local HTTP development and must be set to `True` behind HTTPS.

**Cloudinary upload endpoint (`backend/routers/uploads.py`)**

```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool
from ..deps import current_user
from .. import cloudinary_service

router = APIRouter(prefix="/api/uploads", tags=["uploads"])
MAX_FILES, MAX_BYTES = 15, 10 * 1024 * 1024

@router.post("/images")
async def upload_images(
    files: list[UploadFile] = File(...),
    user: dict = Depends(current_user),
):
    if not cloudinary_service.is_enabled():
        raise HTTPException(status_code=503, detail="Image upload not configured.")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400,
                            detail=f"Upload at most {MAX_FILES} images at once.")
    urls: list[str] = []
    for file in files:
        if not (file.content_type or "").startswith("image/"):
            raise HTTPException(status_code=400,
                detail=f"{file.filename}: only image files are allowed.")
        data = await file.read()
        if len(data) > MAX_BYTES:
            raise HTTPException(status_code=400,
                detail=f"{file.filename}: image exceeds 10 MB.")
        url = await run_in_threadpool(
            cloudinary_service.upload_image, data, file.filename
        )
        urls.append(url)
    return {"ok": True, "urls": urls}
```

Authentication via `Depends(current_user)` rejects unauthenticated requests before any file processing. Because the Cloudinary SDK's `uploader.upload` is synchronous, it is dispatched through `run_in_threadpool` to avoid blocking the asyncio event loop. Each file is validated for MIME type and a 10 MB size cap before upload.

## 5.4 Front-End Implementation

The front end is entirely server-rendered. The Jinja2 `base.html` template defines the shared HTML skeleton; child templates use `{% extends %}` and `{% block content %}` to inject page-specific content without repeating the layout. Context variables such as `user`, `properties`, and `metrics` are passed from the page router to the template engine, so no client-side data-fetching is needed for initial page loads.

`static/js/app.js` (~450 lines) provides a lightweight `API` object wrapping the browser `fetch` API:

```javascript
const API = {
  async request(url, options = {}) {
    const opts = { credentials: "same-origin", headers: {}, ...options };
    if (opts.body && !(opts.body instanceof FormData)) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(url, opts);
    let data = {};
    try { data = await res.json(); } catch (_) { /* empty body */ }
    if (!res.ok) {
      const err = new Error(data.detail || `Request failed (${res.status})`);
      err.status = res.status;
      throw err;
    }
    return data;
  },
  get(url)        { return this.request(url); },
  post(url, body) { return this.request(url, { method: "POST", body }); },
  put(url, body)  { return this.request(url, { method: "PUT", body }); },
  del(url)        { return this.request(url, { method: "DELETE" }); },
};
```

`credentials: "same-origin"` ensures the httpOnly cookie is sent automatically. Plain objects are serialised to JSON with the appropriate header; `FormData` bodies omit the header so the browser sets the correct multipart boundary. Non-OK responses throw a typed `Error` carrying the `detail` field, handled uniformly by callers via `catch (err) { toast(err.message, "error"); }`.

Images are previewed locally with `URL.createObjectURL` but not uploaded until form submission, avoiding orphaned Cloudinary assets:

```javascript
async function resolveImages() {
  const pending = items.filter(i => i.file);  // files not yet uploaded
  let uploaded = [];
  if (pending.length) {
    const fd = new FormData();
    pending.forEach(i => fd.append("files", i.file));
    const res = await API.post("/api/uploads/images", fd);
    uploaded = Array.isArray(res.urls) ? res.urls : [];
  }
  // Merge already-uploaded URLs with newly returned URLs in order
  let u = 0;
  return items.map(it => it.file
    ? (u < uploaded.length ? uploaded[u++] : null)
    : it.url
  ).filter(Boolean);
}
```

On submission, all pending `File` objects are batched into a single multipart `FormData`, the returned URLs are stitched back into their original positions (preserving cover-photo ordering), and only then is the property payload submitted to `POST /api/properties` or `PUT /api/properties/{id}`.

## 5.5 Module Description

The NestQuest backend is organised into six cohesive functional modules implemented as router files under `backend/routers/` and supported by shared services in `backend/`. Figure 5.1 shows the interaction paths between these modules.

[[FIG fig5_1_modules.png | Figure 5.1 — Module interaction overview.]]

Browser requests arrive at the FastAPI application layer and are dispatched to the appropriate router. Each router depends on the shared `database`, `security`, and `deps` helpers; the Upload and ML modules additionally call the Cloudinary and scikit-learn services respectively.

### 5.5.1 Authentication Module

Implemented in `backend/routers/auth.py`, supported by `backend/security.py` and `backend/deps.py`, this module exposes five endpoints under `/api/auth`: `POST /signup`, `POST /login`, `POST /logout`, `GET /me`, and `PUT /me`. Registration normalises the email, checks for duplicates, hashes the password at bcrypt cost 12, and inserts the user document; on success a JWT is stored in an httpOnly cookie. The `ProfileUpdate` schema excludes `role`, `email`, and `password_hash`, preventing privilege escalation through the profile endpoint. The dependency chain `optional_user → current_user → admin_user` in `deps.py` guards all protected routes: `current_user` raises HTTP 401 for missing tokens, and `admin_user` additionally raises HTTP 403 for non-admin roles.

### 5.5.2 Listings and Search Module

Implemented in `backend/routers/properties.py`, this module covers the full property lifecycle: create (`POST`, status `pending`), paginated filtered list (`GET`), single listing with view-counter increment (`GET /{id}`), update by owner or admin (`PUT /{id}`), and cascading delete (`DELETE /{id}`). The list endpoint accepts eleven filter parameters and five sort modes; locality search uses MongoDB `$regex` with case-insensitive flags. The shortlist toggle at `POST /{id}/save` inserts on the first call and deletes on the second, exploiting the unique compound index to prevent duplicates.

### 5.5.3 Enquiry and Shortlist Module

Implemented in `backend/routers/enquiries.py`, this module provides endpoints to create an enquiry, retrieve received or sent enquiries, and post an owner reply. A business-rule guard prevents owners from enquiring about their own listings. When SMTP is enabled, `email_service` dispatches a notification to the listing owner; mail-server failures are logged rather than raised so they do not block the submission. Reply submission transitions the enquiry status from `sent` to `replied` and populates `reply` and `replied_at` fields. The shortlist endpoints (`POST /save`, `GET /saved`) are surfaced through the properties router and rendered on the user dashboard.

### 5.5.4 AI Price-Estimator Module

Implemented in `backend/routers/ml.py` and `backend/ml/predict.py`, this module loads the serialised `model.pkl` (scikit-learn `LinearRegression`) and `columns.pkl` via `joblib.load` wrapped in `@lru_cache`, reading from disk only once per process. `POST /api/ml/predict` accepts twelve input fields, constructs a one-row pandas DataFrame, reindexes to the stored column order, calls `model.predict`, floors the result at zero, and computes a ± max(predicted × 0.08, RMSE) price range. Each prediction is logged to the `predictions` collection. The model is trained on a 545-row synthetic dataset; its R² of 0.6538 on the 109-row test set reflects a modest fit appropriate as a directional guide rather than a precise valuation.

### 5.5.5 Admin Moderation Module

Implemented in `backend/routers/admin.py` and protected entirely by the `admin_user` dependency (HTTP 403 for non-admins), this module provides aggregate stats, filterable property and user lists, role promotion/demotion with a self-modification guard, and cascading user deletion. When an admin sets a listing to `active` via `PATCH /api/properties/{id}/status`, the `verified` field is also set to `True`, providing a trust indicator to buyers. The seeding logic in `backend/seed.py` creates or promotes the admin account from environment variables before the first request.

## 5.6 Testing

### 5.6.1 Testing Strategy

The testing approach spans seven complementary levels. **Unit testing** covers isolated functions (`hash_password`, `verify_password`, `create_access_token`, `format_inr`, `predict`) with no external dependencies. **Integration testing** verifies that `ensure_indexes` runs without error and that CRUD operations produce expected document shapes. **Functional testing** of API endpoints uses FastAPI's `TestClient` (via `httpx`) to cover success paths, authentication guards, and primary error conditions. **System testing** exercises complete user journeys end-to-end: signup, listing, search, shortlist, enquiry, and admin moderation. **Validation testing** confirms that Pydantic models reject malformed inputs and return HTTP 422 or 400 as appropriate. **Security testing** verifies HTTP 401/403 on unprotected access, duplicate-email enforcement, and admin dependency blocking. **UAT** is conducted manually by walking through primary user stories on a local instance with seeded demo data.

### 5.6.2 Test Cases

The table below presents a representative set of test cases drawn from the functional, validation, and security testing phases.

[[TABLE Table 5.3 — Representative test cases.]]
| TC ID | Scenario | Precondition | Input | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| TC-01 | User signup — success | No existing account with email | `POST /api/auth/signup` {name, email, password, phone} | HTTP 201, `ok: true`, `nestquest_token` cookie set | HTTP 201, cookie present | Pass |
| TC-02 | User signup — duplicate email | Account with same email already exists | `POST /api/auth/signup` with existing email | HTTP 409, detail "An account with this email already exists." | HTTP 409, correct message | Pass |
| TC-03 | User login — valid credentials | User account exists | `POST /api/auth/login` {email, password} | HTTP 200, `ok: true`, cookie refreshed | HTTP 200, cookie set | Pass |
| TC-04 | User login — wrong password | User account exists | `POST /api/auth/login` with incorrect password | HTTP 401, detail "Invalid email or password." | HTTP 401, correct message | Pass |
| TC-05 | Access protected route — no token | Not logged in | `GET /api/auth/me` (no cookie) | HTTP 401 | HTTP 401 | Pass |
| TC-06 | Access admin route — non-admin user | Logged in as regular user | `GET /api/admin/stats` with user JWT | HTTP 403 | HTTP 403 | Pass |
| TC-07 | Post listing — authenticated owner | User logged in | `POST /api/properties` with complete valid payload | HTTP 201, `status: "pending"` | HTTP 201, status pending | Pass |
| TC-08 | Post listing — unauthenticated guest | Not logged in | `POST /api/properties` (no cookie) | HTTP 401 | HTTP 401 | Pass |
| TC-09 | Image upload — file exceeds 10 MB | User logged in, Cloudinary configured | `POST /api/uploads/images` with 11 MB PNG | HTTP 400, detail contains "exceeds 10 MB" | HTTP 400, correct detail | Pass |
| TC-10 | Image upload — non-image file | User logged in, Cloudinary configured | `POST /api/uploads/images` with a .pdf file | HTTP 400, detail "only image files are allowed" | HTTP 400, correct detail | Pass |
| TC-11 | Property search by city | At least one active listing exists | `GET /api/properties?city=Mumbai` | HTTP 200, results filtered to city Mumbai | HTTP 200, filtered correctly | Pass |
| TC-12 | Shortlist toggle — save then unsave | User logged in, active listing exists | `POST /api/properties/{id}/save` (twice) | First call: `saved: true`; second call: `saved: false` | Correct toggle behaviour | Pass |
| TC-13 | Send enquiry — owner on own listing | User logged in, listing belongs to same user | `POST /api/enquiries` {property_id: own listing} | HTTP 400, cannot enquire own listing | HTTP 400 | Pass |
| TC-14 | Admin approve listing | Logged in as admin, listing in pending status | `PATCH /api/properties/{id}/status` {status: "active"} | HTTP 200, `status: "active"`, `verified: true` | HTTP 200, both fields updated | Pass |
| TC-15 | Health check | Application running, MongoDB reachable | `GET /api/health` | HTTP 200, `ok: true`, `database: true`, `model_available: true` | HTTP 200, all fields true | Pass |

All fifteen cases were verified by executing the described inputs against a running local instance of NestQuest with demo data seeded. Edge cases not covered here — such as concurrent shortlist toggles, network interruption during Cloudinary upload, and invalid JWT signatures — are identified as areas for future automated regression test coverage.
