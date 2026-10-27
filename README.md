# NestQuest — Property Marketplace (Buy · Rent · Commercial)

A NoBroker-style property marketplace where anyone can create an account, log in,
and post, search, shortlist and enquire about residential and commercial property —
directly with owners, with no brokerage.

Rebuilt from the original Flask "House Price Prediction" ML demo into a full
multi-user marketplace. The original trained model is retained and repurposed as
an **AI price estimator**.

## Tech stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI + Uvicorn |
| Database | MongoDB Atlas (Motor async driver) |
| Templates | Jinja2 (server-rendered) |
| Auth | bcrypt password hashing + JWT in an httpOnly cookie |
| ML | scikit-learn Linear Regression (`model/model.pkl`) |
| Styling | Hand-written CSS (no build step) |
| Email | SMTP (optional, disabled by default) |

## Features

**Guest**
- Browse and search all active listings
- Filter by listing type (buy/rent/commercial), city, property type, budget,
  bedrooms, furnishing; sort by price, area, newest, popularity
- View full property detail with image gallery and similar listings
- AI price estimator (`/insights`)

**Registered user**
- Sign up / log in / log out
- Post, edit and delete own listings
- Shortlist (save) any property
- Send enquiries to owners and reply to enquiries received
- Dashboard with listings, shortlist, received enquiries, sent enquiries
- Edit profile

**Admin**
- Platform statistics
- Approve / reject / feature listings
- View and delete users
- Promote users to admin

## Project structure

```
house-prediction/
├── backend/
│   ├── main.py              FastAPI app, lifespan, exception handlers
│   ├── config.py            .env loader + settings
│   ├── database.py          Mongo client, collections, indexes
│   ├── security.py          bcrypt + JWT
│   ├── models.py            Pydantic schemas
│   ├── deps.py              auth dependencies
│   ├── utils.py             serializers + option lists
│   ├── email_service.py     optional SMTP
│   ├── seed.py              admin + demo data seeding
│   ├── ml/predict.py        AI price estimator
│   └── routers/
│       ├── auth.py          /api/auth/*
│       ├── properties.py    /api/properties/*
│       ├── enquiries.py     /api/enquiries/*
│       ├── admin.py         /api/admin/*
│       ├── ml.py            /api/ml/*
│       └── pages.py         server-rendered pages
├── templates/               Jinja2 pages
├── static/css/style.css     theme
├── static/js/app.js         fetch helpers + UI behaviour
├── model/                   trained model artefacts (reused)
├── data/Housing.csv         original training dataset
├── notebook/                original training notebook
├── run.py                   dev entrypoint
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env      # then fill in DATABASE_URL and JWT_SECRET
python run.py             # http://localhost:8000
```

On first boot the app connects to MongoDB, creates the required indexes, seeds the
admin account and (unless `SEED_DEMO_DATA=false`) inserts 20 demo listings.

## Configuration

All configuration lives in `.env` (gitignored). See `.env.example` for the full list.

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | MongoDB Atlas connection string |
| `DB_NAME` | Database name (default `house`) |
| `JWT_SECRET` | Signing key for auth tokens — set a long random value |
| `JWT_EXPIRE_MINUTES` | Token lifetime (default 7 days) |
| `SMTP_*` | Email notifications; leave `SMTP_ENABLED=false` to disable |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Seeded admin account |
| `SEED_DEMO_DATA` | Insert demo listings on first boot |

## Demo accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@gmail.com` | `Admin@123` |
| Owner | `owner1@demo.com` | `Demo@123` |

Change the admin password before any real deployment.

## API overview

```
POST   /api/auth/signup              create account
POST   /api/auth/login               log in (sets cookie)
POST   /api/auth/logout              log out
GET    /api/auth/me                  current user
PUT    /api/auth/me                  update profile

GET    /api/properties               search / filter / paginate
GET    /api/properties/facets        cities + property types
GET    /api/properties/my            my listings
GET    /api/properties/saved         my shortlist
GET    /api/properties/{id}          detail
POST   /api/properties               create
PUT    /api/properties/{id}          update
DELETE /api/properties/{id}          delete
POST   /api/properties/{id}/save     toggle shortlist
PATCH  /api/properties/{id}/status   admin: moderate

POST   /api/enquiries                send enquiry
GET    /api/enquiries/received       enquiries for my listings
GET    /api/enquiries/sent           enquiries I sent
POST   /api/enquiries/{id}/reply     owner reply

GET    /api/admin/stats              dashboard stats
GET    /api/admin/properties         all listings
GET    /api/admin/users              all users
PATCH  /api/admin/users/{id}/role    change role
DELETE /api/admin/users/{id}         delete user

POST   /api/ml/predict               AI price estimate
GET    /api/ml/status                model availability + metrics
GET    /api/health                   health check
```

Interactive API docs are served at `/docs`.

## Pages

`/` home · `/properties` search · `/property/{id}` detail · `/post` create ·
`/edit/{id}` edit · `/login` · `/signup` · `/dashboard` · `/admin` · `/insights`

## AI price estimator

The original project's Linear Regression model (R² ≈ 0.65, MAE ≈ ₹7.58 L) is reused
unchanged. `POST /api/ml/predict` returns an estimated price plus an expected range
derived from the model's RMSE. Every estimate is logged to the `predictions`
collection. Retrain by running `notebook/house_price_training.ipynb`.

## Notes

- **Images** are stored as public URLs on the listing document. MongoDB Atlas has no
  file storage, so uploads are out of scope; paste image URLs when posting.
- `SMTP_ENABLED=false` by default so the app never attempts to send mail in
  development. Signup and enquiry emails become no-ops.
- The JWT cookie is set with `secure=False` for local HTTP development. Set it to
  `True` behind HTTPS in production.
