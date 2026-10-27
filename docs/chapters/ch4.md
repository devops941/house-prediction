# 4. SYSTEM DESIGN

## 4.1 System Architecture

NestQuest follows a classic three-tier web architecture: a browser-based presentation layer communicates with a **FastAPI**/Uvicorn (ASGI) application tier, which persists data to **MongoDB Atlas** accessed asynchronously via **Motor**. Jinja2 server-side templates render complete HTML pages, eliminating a separate front-end build pipeline. Auxiliary services — **Cloudinary** for image storage and an optional SMTP relay — integrate over HTTPS without affecting page-render latency.

Figure 4.1 illustrates the layered system architecture.

[[FIG fig4_1_architecture.png | Figure 4.1 — Layered system architecture of NestQuest.]]

The application tier is stateless between requests — all session state is in a signed JWT cookie — so the server can be restarted without invalidating sessions (provided `JWT_SECRET` is unchanged). Router modules grouped by domain (`auth`, `properties`, `enquiries`, `admin`, `ml`, `uploads`, `pages`) enable independent testability of each endpoint group [1].

## 4.2 Block Diagram

Figure 4.2 decomposes NestQuest into six major functional subsystems: (1) Authentication and User Management; (2) Property Listings — full lifecycle from creation through admin moderation to publication; (3) Search and Discovery — multi-field filters and text search; (4) Enquiry and Shortlist; (5) AI Price Estimator — thirteen encoded inputs returning a predicted price via a pre-trained scikit-learn Linear Regression model; and (6) Admin Moderation.

[[FIG fig4_2_block.png | Figure 4.2 — Block diagram of the major functional subsystems.]]

Each subsystem maps to one or more FastAPI router modules. The AI Price Estimator is intentionally loosely coupled: `backend/ml/predict.py` consults cached model artefacts without touching the database, so the model can be retrained by replacing `model/model.pkl` and `model/columns.pkl` without changing any router code.

## 4.3 Component Interaction Diagram

**Note on hardware diagrams:** NestQuest is a pure software web application; no custom hardware is involved. This section presents the directly analogous artefact: a component interaction diagram of runtime software module communication.

Figure 4.3 shows runtime relationships among Python modules, the Jinja2 template engine, the Motor driver, and external cloud services.

[[FIG fig4_3_component.png | Figure 4.3 — Component interaction diagram (software modules).]]

`backend/main.py` (the FastAPI application factory) opens the Motor connection pool, calls `ensure_indexes()` idempotently, and invokes `backend/seed.py` to provision the admin account on startup. Inbound requests flow through FastAPI's dependency-injection: `backend/deps.py` decodes the JWT cookie via `backend/security.py` and forwards the resolved user to the appropriate router, which calls database accessors, invokes `backend/cloudinary_service.py` for image uploads, and returns JSON or a Jinja2 `TemplateResponse`. Pydantic v2 models in `backend/models.py` enforce request validation at the network boundary, preventing malformed data from reaching the database [16].

## 4.4 Computing Environment

**Development machine.** Development runs on a Windows 11 Pro workstation with Python 3.12 in a per-project `venv`, launched via `python run.py` (`uvicorn.run` with `reload=True`). Any modern PC with 4 GB RAM and broadband internet suffices, since computationally intensive services are cloud-offloaded.

**Python runtime.** The application tier runs under **Uvicorn** (ASGI, single-process event loop, optional multi-worker). All I/O-bound operations — Motor queries, Cloudinary uploads via `run_in_threadpool` — are awaited asynchronously to keep the event loop unblocked.

**MongoDB Atlas.** The persistence layer is a MongoDB Atlas cluster reached via `DATABASE_URL` in `.env`; Motor maintains a TLS-encrypted connection pool (`certifi` CA bundle). Atlas handles replication, backups, and scaling; the free tier (M0, 512 MB) covers development and low-traffic production.

**Cloudinary.** Images are uploaded server-side via the Cloudinary Python SDK; stable HTTPS URLs are stored in property documents. The application never writes files to local disk, enabling ephemeral or containerised deployment.

**Browser client.** The UI is standard HTML/CSS/JavaScript in any modern browser. Jinja2 templates produce complete pages; `app.js` adds progressive enhancements via HTTP GET/POST and `fetch` API calls.

## 4.5 Software Design

### 4.5.1 Database Schema

NestQuest uses MongoDB with five collections whose schemas are enforced by Pydantic v2 models at the application layer, allowing schema evolution without disruptive migrations.

**users**: unique `email`, bcrypt `password_hash` (cost 12), `role` (`"user"` / `"admin"`), and contact fields. **properties**: `owner_id`, `listing_type`, `property_type`, physical attributes, location, up to fifteen Cloudinary image URLs, `status` (pending / active / rejected / sold / rented), `featured`, `verified`, and a `views` counter. **enquiries**: contact messages linking `property_id`, `owner_id`, and optional `sender_id` (null for guests), with `reply` and `status` supporting an owner-reply workflow. **saved**: minimal `(user_id, property_id, created_at)` tuples with a compound unique index preventing duplicate saves. **predictions**: logs each AI estimator call with input `features`, `predicted_price`, `user_id`, and `created_at`.

Figure 4.5 presents the entity–relationship diagram for all five collections.

[[FIG fig4_5_er.png | Figure 4.5 — Entity–relationship diagram of the MongoDB collections.]]

All cross-collection references (`properties.owner_id`, `enquiries.owner_id`/`sender_id`, `saved.user_id`/`property_id`) point to `users._id` or `properties._id`. Referential integrity is enforced at the application layer: deleting a user cascades to their properties, saved records, and enquiries; deleting a property cascades to its saved and enquiry records. MongoDB does not enforce foreign-key constraints natively, making this cascade logic critical.

Table 4.6 enumerates all indexes maintained by `ensure_indexes()`, designed to support the most frequent query patterns: compound filtering on `(city, listing_type, status)` for the browse page, descending `created_at` for default sort, and a full-text index for keyword search.

[[TABLE Table 4.6 — MongoDB indexes.]]
| Collection | Fields | Options |
|---|---|---|
| users | email | unique |
| properties | city, listing_type, status (compound) | — |
| properties | owner_id | — |
| properties | created_at (desc) | — |
| properties | price | — |
| properties | property_type | — |
| properties | title, description, locality, city | text index `property_text_search` |
| saved | user_id, property_id (compound) | unique |
| enquiries | owner_id, created_at | — |
| enquiries | sender_id, created_at | — |
| predictions | created_at (desc) | — |

The compound index on `(city, listing_type, status)` is most critical since most browse requests specify all three filters; `property_text_search` enables keyword search across four fields simultaneously. All indexes use `pymongo` direction constants and Motor's asynchronous `create_index` [9].

### 4.5.2 Use-Case Model

Three actor types interact with NestQuest: **Guest** (unauthenticated), **Registered User** (authenticated owner or buyer/tenant), and **Admin** (privileged moderator). A Guest may browse, view listings (incrementing the view counter), use the AI estimator, and submit enquiries (`sender_id` = null); protected-page access redirects to `/login?next=<url>`. A Registered User additionally posts listings (triggering admin approval), manages images, edits/deletes own listings, toggles the shortlist, sends enquiries on others' listings, replies to received enquiries, and views their dashboard. An Admin additionally approves, rejects, features, or deletes any listing (setting `active` also sets `verified=True`), manages user accounts including role promotion (except their own), and accesses platform-wide statistics.

Figure 4.4 depicts the use-case diagram with all three actors.

[[FIG fig4_4_usecase.png | Figure 4.4 — Use-case diagram (Guest, Registered User, Admin).]]

Owner-specific actions (edit, reply) are distinct from buyer-specific actions (enquire, shortlist). The system prevents owners from enquiring on or shortlisting their own listings, enforced in the API endpoints by comparing the authenticated user to `owner_id`.

### 4.5.3 Data-Flow Diagrams

The Level 0 DFD in Figure 4.6 shows NestQuest as a single process with three external entities: **User**, **Admin**, and **External Services** (MongoDB Atlas and Cloudinary). Users send queries, enquiries, and estimator inputs; the Admin sends moderation decisions; External Services provide bi-directional storage and image CDN flows.

[[FIG fig4_6_dfd0.png | Figure 4.6 — Data-flow diagram, context level (Level 0).]]

Figure 4.7 expands into Level 1 with six sub-processes: Authentication, Property Management, Search and Browse, Enquiry Handling, AI Price Estimation, and Admin Operations, each connected to the relevant data stores and external entities.

[[FIG fig4_7_dfd1.png | Figure 4.7 — Data-flow diagram, Level 1.]]

Authentication is the gateway issuing tokens consumed by all other sub-processes. Search and Browse reads the properties store without writing, making the read path independently scalable. AI Price Estimation reads only in-memory cached model artefacts and writes a single log record per call.

### 4.5.4 Sequence Design

Figure 4.8 illustrates the most complex multi-step user journey — posting a listing with image uploads — involving the browser, FastAPI, Cloudinary, and MongoDB Atlas, whose correct sequencing prevents orphaned image files.

[[FIG fig4_8_sequence.png | Figure 4.8 — Sequence diagram: posting a listing with image upload.]]

An authenticated user navigates to `/post`; `page_user` validates the JWT and renders the form. Images are **not** uploaded on file selection; `app.js` defers upload to the "Publish" click. `POST /api/uploads/images` then validates each file (MIME `image/*`, ≤10 MB, ≤15 files) and calls `cloudinary_service.upload_image()` concurrently via `run_in_threadpool`. Cloudinary returns secure HTTPS URLs, injected as hidden form fields before the listing is submitted to `POST /api/properties`, inserted into MongoDB with `status="pending"` and `verified=False`, and queued for admin approval. The deferred-upload design prevents orphaned Cloudinary assets.

### 4.5.5 API Design

NestQuest exposes seven REST-style endpoint groups under `/api/`, plus server-rendered page routes, auto-documented at `/docs` (Swagger UI) and `/redoc` [1].

**Auth** (`/api/auth`): registration, login (sets httpOnly JWT cookie), logout, profile retrieval, and profile update (only `name`, `phone`, `about` — preventing privilege escalation). **Properties** (`/api/properties`): paginated browsing with fourteen filter parameters and five sort options, facet counts, owner-specific retrieval, shortlist management, and create/update/delete/status-patch (`limit` capped at 60). **Enquiries** (`/api/enquiries`): create (guests allowed; owners blocked on own listings), retrieve sent/received, and reply (sets status `"replied"`). **Admin** (`/api/admin`): platform statistics, property and user management, role-change and user-delete (with self-action guards), and status moderation. **ML** (`/api/ml`): `POST /predict` (thirteen inputs → `predicted_price`, `price_range`, INR-formatted labels) and `GET /status`. **Uploads** (`/api/uploads`): Cloudinary status check and authenticated multipart image upload. **Health** (`/api/health`): `ok`, `app`, `database`, and `model_available` fields for monitoring.

### 4.5.6 Authentication and Security Design

Security rests on three mechanisms: bcrypt password hashing, JWT session management, and role-based access control via FastAPI dependency injection.

Passwords are hashed with `bcrypt.gensalt(rounds=12)` (2¹² = 4 096 iterations); `verify_password` wraps `bcrypt.checkpw` in a try/except to prevent leakage from malformed inputs [6]. On login, the server issues a JWT with claims `sub`, `role`, `iat`, and `exp` (7-day default), signed HS256 with `JWT_SECRET`, set as an httpOnly SameSite=Lax cookie (`nestquest_token`) to mitigate XSS token theft; an `Authorization: Bearer` header is also accepted for API clients [7].

The dependency chain has three levels: `optional_user` (user or `None`), `current_user` (HTTP 401 if unauthenticated), and `admin_user` (HTTP 403 if role ≠ `"admin"`). Page routes use `page_user`, which redirects to `/login?next=<url>` instead of raising an HTTP error. All authorisation logic is centralised in `backend/deps.py`, consistent with OWASP Top 10 guidance [8].

### 4.5.7 Deployment Architecture

Figure 4.10 shows the deployment diagram across three zones: developer workstation, cloud application host, and external managed services.

[[FIG fig4_10_deployment.png | Figure 4.10 — Deployment diagram.]]

Locally, `python run.py` launches Uvicorn in single-process reload mode. For production, the application runs on a Linux VPS or container platform with a service supervisor (systemd) for automatic restarts; the Uvicorn process (port 8000) would sit behind a reverse proxy (Nginx or Caddy) for TLS termination and rate limiting — currently future work. MongoDB Atlas and Cloudinary are reached over TLS/HTTPS with credentials in environment variables; Atlas additionally enforces IP allowlisting. The fully stateless application tier can be redeployed or scaled horizontally without any data migration.

## 4.6 Flowchart

Figure 4.9 traces the complete property-posting workflow — authentication checks, form validation, image upload, and admin moderation — selected because it traverses the most subsystems and shows the conditional paths determining whether a listing reaches the live marketplace.

[[FIG fig4_9_flowchart.png | Figure 4.9 — Flowchart of the property-posting workflow.]]

The workflow starts at `/post`; unauthenticated users redirect to `/login?next=/post`. Once authenticated, the user completes the form; JavaScript defers image upload to the Publish click. Each file is validated (MIME type, ≤10 MB); non-conforming files trigger an error toast without aborting submission. Valid files upload in parallel to Cloudinary via `/api/uploads/images`; returned URLs are injected into the form before it is POSTed to `/api/properties` with `status="pending"`. Pydantic validation failures return HTTP 422; on success the document enters the moderation queue. An admin setting `"active"` also sets `verified=True`, surfacing a verification badge on the property card.

Edit and delete are alternative terminal states: an owner may update fields or images at `/edit/{id}`, or delete the listing, which cascades to remove associated saved records and enquiries.
