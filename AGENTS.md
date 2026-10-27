# AGENTS.md — NestQuest (house-prediction)

## What this project is

A NoBroker-style property marketplace (Buy / Rent / Commercial) with user accounts.
Originally a single-purpose Flask ML demo; rebuilt in place. The old Flask `app.py`
and its templates were removed. The trained model was kept and repurposed.

## Architecture

- **FastAPI + Uvicorn** backend, **Jinja2 server-rendered** pages (no JS build step).
- **MongoDB Atlas** via Motor (async). Collections: `users`, `properties`,
  `enquiries`, `saved`, `predictions`. Database name from `DB_NAME` (default `house`).
- **Auth**: bcrypt hashing + JWT stored in the `nestquest_token` httpOnly cookie.
  `optional_user` returns None for guests; `current_user` raises 401; `admin_user`
  raises 403. Page routes redirect guests to `/login?next=...` via the exception
  handler in `main.py`.
- **ML**: `backend/ml/predict.py` wraps `model/model.pkl` as an AI price estimator.
  Do not confuse `backend.ml.predict` with `backend.routers.ml` — they are different
  modules. `main.py` imports the engine as `ml_engine` and the router as `ml_router`
  precisely to avoid this shadowing.

## Layout

```
backend/main.py          app factory, lifespan, exception handlers
backend/config.py        minimal .env loader + Settings (no python-dotenv dep)
backend/database.py      client, collection accessors, ensure_indexes()
backend/security.py      bcrypt + JWT
backend/models.py        all Pydantic schemas
backend/deps.py          auth deps + to_object_id
backend/utils.py         serialize_user / serialize_property + option lists
backend/seed.py          admin + 20 demo listings
backend/routers/*.py     auth, properties, enquiries, admin, ml, pages
templates/               base.html + pages; _card.html is the property-card macro
static/js/app.js         fetch helpers (API, toast), all page behaviour
static/css/style.css     whole theme
```

## Conventions and gotchas

- **`TemplateResponse` must be called as `TemplateResponse(request, "name.html", ctx)`**
  with the request first. The old `(name, ctx)` signature fails with
  `TypeError: unhashable type: 'dict'`.
- `serialize_user` lives in `backend/utils.py`, not `backend/deps.py`.
- `_ctx(request, user, **extra)` builds the template context and always injects
  `current_user` (a serialized dict or None).
- Every template that uses `app.js` auth helpers must set
  `window.NESTQUEST_AUTH = true|false` in a `{% block scripts %}`.
- Listings with `status != "active"` are only visible to their owner and to admins.
- Images are **URLs on the document**, not uploads (Atlas has no blob storage).
- Indexes are created in `database.ensure_indexes()` on every boot; it is idempotent.
- `SEED_DEMO_DATA` gates demo listings; seeding is skipped if any property exists.
- SMTP is off unless `SMTP_ENABLED=true`; email failures are logged, never raised.

## Commands

```bash
pip install -r requirements.txt
python run.py                    # dev server on :8000
python -c "from backend.main import app; print('ok')"   # fast import check
curl -s localhost:8000/api/health
```

## Verification checklist

After changing backend or templates, confirm:
1. `python -c "from backend.main import app"` imports cleanly.
2. `/api/health` returns `{"ok":true,"database":true,...}`.
3. `/`, `/properties`, `/login`, `/signup`, `/insights` all return 200.
4. `/post` and `/dashboard` return 303 to `/login?next=...` for guests.
5. `POST /api/ml/predict` returns a price.
6. Signup → create listing → save → enquiry → reply works end to end.

## Secrets

`.env` holds the Mongo URI, JWT secret and SMTP credentials and is gitignored.
Never commit it. `.env.example` documents the keys with placeholder values.
