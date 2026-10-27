# NestQuest — Report Writing Facts & Specification (shared by all chapter agents)

You are writing part of a university final-year project report. Read this whole file, then
write ONLY your assigned chapter file in the constrained Markdown described in Section 0.
Use ONLY facts stated here (or generic domain knowledge). NEVER invent institutional/personal
details, exam results, or research citations beyond the reference list in Section 5.

---

## 0. OUTPUT FORMAT — CONSTRAINED MARKDOWN (strict)

Write plain UTF-8 Markdown using ONLY these constructs (a custom converter renders them to Word):

- `# N. TITLE` — chapter heading (one per file, first line). Example: `# 4. SYSTEM DESIGN`
- `## N.M Title` — section heading. Example: `## 4.1 System Architecture`
- `### N.M.K Title` — subsection. Example: `#### 3.4.1 Technical Feasibility` (use `####` for 4th level)
- Normal paragraphs: plain text, one blank line between paragraphs. Write FULL paragraphs
  (4–8 sentences), formal academic English, third person. No "I/we will".
- Bold inline with `**text**`; inline code with backticks `` `like_this` ``. (Only these two inline styles.)
- Bullet list: lines starting `- `. Numbered list: lines starting `1. ` `2. ` ...
- Figure (schematic, lives in docs/figures/): a line on its own:
  `[[FIG filename.png | Figure N.M — Caption sentence.]]`
- EDA chart (lives in static/images/): `[[EDA filename.png | Figure N.M — Caption.]]`
- Screenshot placeholder (Annexure B style): `[[SHOT | Figure B.x — What to capture.]]`
- Table: put a caption line `[[TABLE Table N.M — Caption.]]` immediately BEFORE a GitHub table:
  ```
  [[TABLE Table 4.6 — MongoDB indexes.]]
  | Collection | Fields | Options |
  |---|---|---|
  | users | email | unique |
  ```
- Code block: standard fenced block with a language tag, e.g. ```python ... ``` or ```bash ... ```
- `[[PAGEBREAK]]` on its own line forces a page break (use sparingly, e.g. before big code annexes).
- Placeholder for unknown facts: write `[TO BE FILLED: ...]` in square brackets so it is visible.

Every figure and every table MUST be referenced in the prose (e.g. "as shown in Figure 4.1")
AND be followed/preceded by an explanatory paragraph. Do not emit a figure/table with no explanation.

Keep headings EXACTLY at the numbers assigned in Section 6. Do not add or renumber chapters.

---

## 1. PROJECT IDENTITY

- **Project title:** NestQuest — A Brokerage-Free Property Marketplace with an AI Price Estimator
- **Category:** Web Application + Machine Learning
- **Project type:** [TO BE FILLED: Individual / Team] (use placeholder)
- **Course / Department / College / Academic Year / Student name(s) / Register no. / Guide:**
  all UNKNOWN — always write them as placeholders like `[College Name]`, `[Student Name]`,
  `[Register Number]`, `[Guide Name]`, `[Academic Year]`. Do NOT invent them.
- **One-line problem:** Property search in India is dominated by brokers, causing opaque pricing,
  brokerage fees (typically 1–2% or one month's rent), information asymmetry and slow deals.
- **One-line solution:** A self-service, server-rendered web platform where owners post listings
  for free and buyers/tenants search, shortlist and enquire directly with owners — augmented by a
  scikit-learn price estimator that gives an instant fair-price guide.
- **History:** The codebase began as a single-purpose Flask "house price prediction" ML demo and was
  rebuilt in place into the NestQuest FastAPI marketplace; the trained regression model was retained
  and repurposed as the AI price estimator.

### Technology stack (authoritative)
- Backend framework: **FastAPI** on **Uvicorn** (ASGI), Python 3.12/3.14.
- Templating: **Jinja2** server-rendered HTML (no JS build step).
- Front end: hand-written **CSS** (`static/css/style.css`, ~460 lines) + vanilla **JavaScript**
  (`static/js/app.js`, ~450 lines, a small `fetch` wrapper `API`, toast, page behaviours).
- Database: **MongoDB Atlas** (cloud) via **Motor** (async driver); `pymongo`, `certifi` for TLS.
- Auth: **bcrypt** password hashing (cost factor 12) + **JWT** (PyJWT, HS256) stored in an
  httpOnly cookie named `nestquest_token`.
- ML: **scikit-learn** Linear Regression, **pandas**, **numpy**, **joblib**; EDA with
  **matplotlib** + **seaborn**.
- Image uploads: **Cloudinary** (server-side upload, secret kept on server).
- Email: **SMTP** via Python `smtplib` (optional, disabled by default).
- Validation: **Pydantic** v2 models.

---

## 2. FIGURE CATALOGUE (use exactly these ids, captions, and chapter placement)

Schematic figures (folder docs/figures/, reference with `[[FIG ...]]`):
- `fig3_1_existing.png` — Figure 3.1 — Workflow of the existing broker-mediated process.
- `fig3_2_proposed.png` — Figure 3.2 — Workflow of the proposed NestQuest system.
- `fig4_1_architecture.png` — Figure 4.1 — Layered system architecture of NestQuest.
- `fig4_2_block.png` — Figure 4.2 — Block diagram of the major functional subsystems.
- `fig4_3_component.png` — Figure 4.3 — Component interaction diagram (software modules).
- `fig4_4_usecase.png` — Figure 4.4 — Use-case diagram (Guest, Registered User, Admin).
- `fig4_5_er.png` — Figure 4.5 — Entity–relationship diagram of the MongoDB collections.
- `fig4_6_dfd0.png` — Figure 4.6 — Data-flow diagram, context level (Level 0).
- `fig4_7_dfd1.png` — Figure 4.7 — Data-flow diagram, Level 1.
- `fig4_8_sequence.png` — Figure 4.8 — Sequence diagram: posting a listing with image upload.
- `fig4_9_flowchart.png` — Figure 4.9 — Flowchart of the property-posting workflow.
- `fig4_10_deployment.png` — Figure 4.10 — Deployment diagram.
- `fig5_1_modules.png` — Figure 5.1 — Module interaction overview.

EDA charts (folder static/images/, reference with `[[EDA ...]]`, use in Chapter 6):
- `price_distribution.png` — Figure 6.1 — Distribution of house prices (histogram + KDE).
- `area_vs_price.png` — Figure 6.2 — Built-up area vs price, coloured by furnishing status.
- `bedrooms_boxplot.png` — Figure 6.3 — Price distribution by number of bedrooms.
- `correlation_heatmap.png` — Figure 6.4 — Correlation heatmap of numeric features.
- `actual_vs_predicted.png` — Figure 6.5 — Actual vs predicted price (Linear Regression & Decision Tree).

Screenshots (Annexure B, handled by the build script — chapter agents may reference
"see Annexure B" but need not emit `[[SHOT]]` unless noted).

---

## 3. TABLE DATA (render these where your chapter brief says so)

**Table 3.1 — Existing vs proposed system**
| Aspect | Existing (broker-led portals) | Proposed (NestQuest) |
|---|---|---|
| Intermediary | Broker / agent | None — owner to buyer direct |
| Brokerage cost | 1–2% of sale / 1 month rent | Zero |
| Pricing transparency | Opaque, negotiated | AI fair-price estimate + listed price |
| Posting | Often paid / broker-gated | Free self-service |
| Moderation | Minimal | Admin approval + featured flags |
| Data ownership | Portal/broker | Platform + verified owners |
| Access | Business hours | 24×7 web self-service |

**Table 4.6 — MongoDB indexes**
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

**Table 6.1 — Model performance (test set, 109 rows)**
| Metric | Linear Regression (selected) | Decision Tree (CART, baseline) |
|---|---|---|
| R² | 0.6538 | 0.4138 |
| MAE | ₹7,58,066 | ₹9,63,666 |
| RMSE | ₹9,39,058 | ₹12,21,894 |

Dataset: 545 rows, 80/20 split = 436 train / 109 test.

**Environment variables (Table 5.2)** — keys only, values are secrets:
`DATABASE_URL, DB_NAME, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, SMTP_* , SMTP_ENABLED,
CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD,
ADMIN_NAME, SEED_DEMO_DATA, APP_NAME`.

---

## 4. TECHNICAL FACTS (authoritative — do not contradict)

### 4.1 Backend layout
```
backend/main.py        app factory, lifespan (connect→index→seed), exception handlers, /api/health
backend/config.py      minimal .env loader + Settings singleton (lru_cache)
backend/database.py    Motor client, collection accessors, ensure_indexes()
backend/security.py    bcrypt hash/verify, JWT create/decode, COOKIE_NAME="nestquest_token"
backend/models.py      Pydantic v2 schemas
backend/deps.py        optional_user → current_user → admin_user, page_user, to_object_id
backend/utils.py       serialize_user, serialize_property, option lists
backend/seed.py        admin + 20 demo listings
backend/email_service.py  optional SMTP
backend/cloudinary_service.py  Cloudinary config + upload_image()
backend/ml/predict.py  AI price estimator
backend/routers/*.py   auth, properties, enquiries, admin, ml, uploads, pages
templates/*.html       base + pages; _card.html card macro
static/css/style.css, static/js/app.js
model/{model.pkl, columns.pkl, metrics.json}, data/Housing.csv, notebook/house_price_training.ipynb
```

### 4.2 Collections & key documents
- `users`: _id, name, email (unique), password_hash (bcrypt), phone, about, role ("user"|"admin"), created_at.
- `properties`: _id, owner_id (FK users), title, description, listing_type (buy|rent|commercial),
  property_type (10 types), price, area_sqft, bedrooms, bathrooms, balconies, floor, total_floors,
  furnishing, facing, age_years, city, locality, address, pincode, amenities[] (≤15), images[] (≤15),
  contact_name, contact_phone, status (pending|active|rejected|sold|rented), featured (bool),
  verified (bool), views (int), created_at.
- `enquiries`: _id, property_id, owner_id, sender_id (None for guests), sender_name, sender_email,
  message, phone, reply, status (sent|replied), created_at, replied_at.
- `saved`: _id, user_id, property_id, created_at (unique compound index → one shortlist per user/property).
- `predictions`: _id, user_id (or None), features{}, predicted_price, created_at.

### 4.3 Security & auth
- Passwords hashed with `bcrypt.gensalt(rounds=12)`; `verify_password` is exception-safe.
- JWT payload: `sub` (user id), `role`, `iat`, `exp`; signed HS256 with `JWT_SECRET`;
  default lifetime `JWT_EXPIRE_MINUTES=10080` (7 days).
- Token carried in httpOnly cookie `nestquest_token` (samesite=lax, secure=False for local HTTP,
  max_age = expire_minutes×60); also accepted via `Authorization: Bearer`.
- Dependency chain: `optional_user` (None for guests) → `current_user` (401 if missing) →
  `admin_user` (403 if role≠admin). Page routes use 303 redirect to `/login?next=...`.
- `ProfileUpdate` exposes only name/phone/about — role/email/password are NOT user-updatable.

### 4.4 Full API surface (prefix shown)
- `/api/auth`: POST signup (name,email,password,phone; 409 on duplicate), POST login (sets cookie),
  POST logout, GET me (+listings_count), PUT me (name/phone/about only).
- `/api/properties`: GET list (filters: listing_type, property_type, city, locality, q, min_price,
  max_price, bedrooms, furnishing, min_area, max_area; sort: newest|price_asc|price_desc|area_desc|popular;
  page, limit≤60), GET facets, GET my, GET saved, GET {id} (increments views for non-owners),
  POST create, PUT {id} (owner/admin), DELETE {id} (cascades to saved+enquiries),
  POST {id}/save (toggle shortlist), PATCH {id}/status (admin moderation; active ⇒ verified=True).
  Search uses MongoDB `$regex` (city exact ^..$ i, locality substring i, q $or across title/
  description/locality/city).
- `/api/enquiries`: POST create (emails owner; owner cannot enquire own listing), GET received,
  GET sent, POST {id}/reply (owner/admin → status "replied").
- `/api/admin`: GET stats, GET properties (optional status filter), GET users (+listings_count),
  PATCH users/{id}/role (cannot change own), DELETE users/{id} (cannot self-delete; cascades).
- `/api/ml`: POST predict (12 inputs → price + range; logs to predictions), GET status (available+metrics).
- `/api/uploads`: GET status (enabled?), POST images (auth; multipart `files`; ≤15 files, ≤10 MB each,
  image/* only; uploads to Cloudinary via run_in_threadpool; returns {urls}; 503/400/502 on error).
- Pages (no prefix): `/`, `/properties`, `/property/{id}`, `/post`, `/edit/{id}`, `/login`, `/signup`,
  `/dashboard`, `/admin`, `/insights`. Guests on protected pages get 303 → `/login?next=`.
- `/api/health`: {ok, app, database, model_available}.
- Static asset cache-buster: `?v={asset_version}` where asset_version = max mtime of style.css & app.js.

### 4.5 ML / AI price estimator (authoritative + HONESTY notes)
- Loads `model/model.pkl` (sklearn LinearRegression) and `model/columns.pkl` (13 feature columns)
  with joblib + lru_cache. `is_available()` true only if both load.
- Input features (13 after encoding): area, bedrooms, bathrooms, stories, mainroad, guestroom,
  basement, hotwaterheating, airconditioning, parking, prefarea,
  furnishingstatus_semi-furnished, furnishingstatus_unfurnished (furnished = dropped reference).
- Inference: build a one-row DataFrame, `.reindex(columns=columns, fill_value=0)`, predict,
  floor at 0. Range = ± max(price×0.08, RMSE). INR formatting via `format_inr`/`short_inr`;
  rent listings get a `/mo` suffix.
- Metrics (model/metrics.json): best_model "Linear Regression";
  Linear Regression r2=0.6538, mae=758066, rmse=939058; Decision Tree r2=0.4138, mae=963666,
  rmse=1221894; n_rows=545, n_train=436, n_test=109. (No training_date or feature list in the JSON.)
- Dataset (data/Housing.csv): 545 rows, columns price, area, bedrooms, bathrooms, stories, mainroad,
  guestroom, basement, hotwaterheating, airconditioning, parking, prefarea, furnishingstatus.
- **HONESTY — dataset provenance:** `scripts/generate_dataset.py` **synthesises** all 545 rows from a
  fixed linear formula + Gaussian noise (numpy seed 42); the file's docstring says it "mirrors the
  structure and statistical shape of the Kaggle 'Housing Prices Dataset' (Yasser H.)". The report must
  describe the dataset HONESTLY as a **synthetic dataset modelled on the structure of that public
  Kaggle dataset**, NOT as the real Kaggle data. Note that because the generator is linear, a linear
  model is expected to fit well (R²≈0.65) — state this as a limitation.
- `decision_tree.py` is a from-scratch CART regression tree (greedy SSE splits, max_depth=5,
  min_samples_split=10). It exists because this machine's Application Control (WDAC) policy blocked
  scikit-learn's compiled tree extension; it is a drop-in used ONLY for training-time comparison.
  At runtime only the Linear Regression `model.pkl` is served.
- Training notebook steps: imports → load CSV → preprocess (map yes/no→1/0 for 6 binary cols;
  one-hot furnishingstatus with drop_first) → EDA (the 5 charts) → train/test split (test_size=0.2,
  random_state=42) → train LinearRegression + custom CART → evaluate (R²/MAE/RMSE) → select best by
  R² → save model.pkl, columns.pkl, metrics.json.
- Predictions ARE logged: the `/api/ml/predict` router inserts {user_id, features, predicted_price,
  created_at} into the `predictions` collection (not inside predict.py itself).

### 4.6 Seeding & ops
- On boot: connect Mongo → ensure_indexes() (idempotent) → seed_admin() → seed_demo_properties().
- seed_admin: creates admin from ADMIN_EMAIL/ADMIN_PASSWORD; if that email already exists as a normal
  user it is promoted to admin (note as a minor risk).
- seed_demo: only if SEED_DEMO_DATA true AND properties empty; inserts 4 demo owners + 20 listings
  (8 buy, 6 rent, 6 commercial) with deterministic RNG seed 2024.
- SMTP: disabled unless SMTP_ENABLED=true; failures are logged, never raised.
- Cloudinary uploads deferred to the "Publish" action on the post form (files uploaded only when the
  listing is saved, avoiding orphaned images).

### 4.7 Known limitations / honest caveats (use in Ch6 discussion, Ch8 limitations)
- Synthetic dataset ⇒ metrics reflect a generated linear relationship, not real market data.
- Linear Regression R²≈0.65 is modest; it is a guide, not a valuation.
- Default `JWT_SECRET` is insecure if unset in production; cookie `secure=False` for local HTTP.
- Search `$regex` on user input is not escaped (ReDoS/regex-injection risk) — note as future work.
- No CSRF token; admin list endpoints are uncapped-by-design (to_list 500/1000).
- Images are external URLs/Cloudinary, not validated for content.

---

## 5. REFERENCES (GENUINE — cite with [n]; Annexure C lists these exact entries)

Use ONLY these. Do NOT invent papers, authors, years, DOIs. For the Literature Survey, treat
[1]–[6] as the technical/academic sources and [12]–[15] as real industry "existing solutions".

[1] S. Ramírez, "FastAPI — Modern, Fast Web Framework for Building APIs with Python," official documentation, https://fastapi.tiangolo.com (accessed 2026).
[2] F. Pedregosa et al., "Scikit-learn: Machine Learning in Python," Journal of Machine Learning Research, vol. 12, pp. 2825–2830, 2011.
[3] T. Hastie, R. Tibshirani, and J. Friedman, "The Elements of Statistical Learning: Data Mining, Inference, and Prediction," 2nd ed., Springer, 2009.
[4] W. McKinney, "Data Structures for Statistical Computing in Python," in Proc. 9th Python in Science Conf. (SciPy), pp. 51–56, 2010.
[5] C. R. Harris et al., "Array Programming with NumPy," Nature, vol. 585, pp. 357–362, 2020.
[6] N. Provos and D. Mazières, "A Future-Adaptable Password Scheme," in Proc. USENIX Annual Technical Conf., 1999.
[7] M. Jones, J. Bradley, and N. Sakimura, "JSON Web Token (JWT)," RFC 7519, IETF, 2015.
[8] OWASP Foundation, "OWASP Top 10 — 2021," https://owasp.org/Top10/ (accessed 2026).
[9] MongoDB Inc., "MongoDB Manual," official documentation, https://www.mongodb.com/docs/ (accessed 2026).
[10] A. Ronacher, "Jinja2 Documentation," Pallets Projects, https://jinja.palletsprojects.com (accessed 2026).
[11] Cloudinary Ltd., "Cloudinary Documentation — Image and Video Upload API," https://cloudinary.com/documentation (accessed 2026).
[12] NoBroker Technologies, "Brokerage-free property platform," https://www.nobroker.in (accessed 2026).
[13] Info Edge (India) Ltd., "99acres real-estate portal," https://www.99acres.com (accessed 2026).
[14] Magicbricks Realty Services, "Magicbricks property portal," https://www.magicbricks.com (accessed 2026).
[15] Zillow Group, "Zestimate home-valuation methodology," https://www.zillow.com/z/zestimate/ (accessed 2026).
[16] S. Bradski and Pydantic contributors, "Pydantic v2 Documentation — Data Validation for Python," https://docs.pydantic.dev (accessed 2026).

---

## 6. PER-CHAPTER BRIEFS (write only your assigned chapter)

**abstract.md** → a single file whose only content is 2 paragraphs (~250–300 words) of abstract text,
NO heading markers (the build script adds the "ABSTRACT" heading). Cover: problem, solution,
tech stack, ML estimator + honest metrics (R²≈0.65 on a synthetic dataset), key outcomes.

**ch1.md → `# 1. INTRODUCTION`** (~1900 words). Sections:
`## 1.1 Overview of the Project`, `## 1.2 Background of the Study`, `## 1.3 Problem Statement`,
`## 1.4 Existing System` (render Table 3.1-style comparison but number it `[[TABLE Table 1.1 — Existing portals vs NestQuest.]]` using the Table 3.1 data), `## 1.5 Objectives of the Project`
(1 primary + 6–8 secondary, measurable), `## 1.6 Scope of the Project`. Reference the domain with [12]–[15].

**ch2.md → `# 2. LITERATURE SURVEY`** (~1800 words). Intro paragraph; `## 2.1 Review of Related Work`
(discuss [2],[3] for regression/CART, [4],[5] data tooling, [6] bcrypt, [7] JWT, [8] OWASP, [1],[9],[10] frameworks);
`## 2.2 Review of Existing Platforms` ([12]–[15], methodology/findings/limitations each);
`## 2.3 Comparison of Approaches` (a `[[TABLE Table 2.1 — ...]]`); `## 2.4 Research Gaps Identified`;
`## 2.5 How the Proposed System Addresses the Gaps`; `## 2.6 Summary`. Every claim cites [n]. Do not invent sources.

**ch3.md → `# 3. SYSTEM ANALYSIS`** (~2200 words). `## 3.1 Existing System Methodology` (use `[[FIG fig3_1_existing.png ...]]`),
`## 3.2 Proposed System Architecture` (use `[[FIG fig3_2_proposed.png ...]]`), `## 3.3 Advantages of the Proposed System`
(render `[[TABLE Table 3.1 — Existing vs proposed system.]]`), `## 3.4 Feasibility Study` with
`#### 3.4.1 Technical Feasibility`, `#### 3.4.2 Economic Feasibility` (give a clearly-labelled ESTIMATED cost
table `[[TABLE Table 3.2 — Indicative cost estimate.]]`: items like MongoDB Atlas free/shared tier,
Cloudinary free tier, VPS hosting ~₹400–800/mo, domain ~₹900/yr, developer time — mark all as estimates),
`#### 3.4.3 Operational Feasibility`.

**ch4.md → `# 4. SYSTEM DESIGN`** (~3000 words, diagram-heavy). Sections and figures:
`## 4.1 System Architecture` (`[[FIG fig4_1_architecture.png ...]]`),
`## 4.2 Block Diagram` (`[[FIG fig4_2_block.png ...]]`),
`## 4.3 Component Interaction Diagram` (software project — explicitly state hardware/circuit diagrams are
not applicable; use `[[FIG fig4_3_component.png ...]]`),
`## 4.4 Computing Environment` (replaces "Hardware Design" for a software project: dev machine, Python
runtime, Atlas cloud DB, Cloudinary, browser — no circuitry),
`## 4.5 Software Design` with `#### 4.5.1 Database Schema` (describe the 5 collections + `[[FIG fig4_5_er.png ...]]`
+ `[[TABLE Table 4.6 — MongoDB indexes.]]`), `#### 4.5.2 Use-Case Model` (`[[FIG fig4_4_usecase.png ...]]`),
`#### 4.5.3 Data-Flow Diagrams` (`[[FIG fig4_6_dfd0.png ...]]` and `[[FIG fig4_7_dfd1.png ...]]`),
`#### 4.5.4 Sequence Design` (`[[FIG fig4_8_sequence.png ...]]`), `#### 4.5.5 API Design` (summarise the
endpoint groups from Section 4.4), `#### 4.5.6 Authentication & Security Design`, `#### 4.5.7 Deployment
Architecture` (`[[FIG fig4_10_deployment.png ...]]`), `## 4.6 Flowchart` (`[[FIG fig4_9_flowchart.png ...]]`).

**ch5.md → `# 5. IMPLEMENTATION`** (~3200 words, include real code). Sections:
`## 5.1 Computing Environment Setup` (venv, pip install -r requirements.txt, .env, python run.py),
`## 5.2 Project Structure` (a ```text code block of the tree from Section 4.1), `[[TABLE Table 5.1 — Key
dependencies.]]`, `[[TABLE Table 5.2 — Environment variables.]]` (keys only),
`## 5.3 Backend Implementation` with short honest code snippets (use ```python blocks) for: the Settings
loader idea, security hash/JWT, a Motor index, a router endpoint (e.g. create property or login), and the
Cloudinary upload endpoint; each snippet followed by explanation. Keep snippets ≤25 lines, representative
not copy-pasted verbatim if unsure — but consistent with Section 4 facts.
`## 5.4 Front-End Implementation` (Jinja2 base + app.js fetch wrapper + the deferred Cloudinary uploader),
`## 5.5 Module Description` with `#### 5.5.1 Authentication Module`, `#### 5.5.2 Listings & Search Module`,
`#### 5.5.3 Enquiry & Shortlist Module`, `#### 5.5.4 AI Price-Estimator Module`, `#### 5.5.5 Admin
Moderation Module`, and add `[[FIG fig5_1_modules.png ...]]` in 5.5.
`## 5.6 Testing` with `#### 5.6.1 Testing Strategy` (unit/integration/system/functional/validation/security/UAT),
and `#### 5.6.2 Test Cases` rendering `[[TABLE Table 5.3 — Representative test cases.]]` with columns
`| TC ID | Scenario | Precondition | Input | Expected | Actual | Status |` — write 12–15 realistic rows
covering signup/login, duplicate email, post listing, image upload validation (>10MB, non-image),
search/filter, shortlist toggle, enquiry+reply, admin moderation, ml predict, guest redirect, health check.
Mark rows as "Pass" only for behaviours supported by the facts; note any as "Planned" if not yet executed.

**ch6.md → `# 6. RESULTS AND DISCUSSION`** (~1900 words). `## 6.1 Experimental Setup` (`[[TABLE Table 6.2 —
Experimental setup.]]`: Python 3.12, FastAPI/Uvicorn, MongoDB Atlas, dataset 545 rows synthetic, 80/20 split),
`## 6.2 Exploratory Data Analysis` (embed all 5 EDA charts `[[EDA ...]]` as Figures 6.1–6.5 with explanation),
`## 6.3 Model Performance` (`[[TABLE Table 6.1 — Model performance.]]` + interpret R²/MAE/RMSE; be honest),
`## 6.4 Application Output` (describe the running pages; reference Annexure B screenshots),
`## 6.5 Discussion` (compare to objectives; strengths; honest limitations from Section 4.7).

**ch7.md → `# 7. RESULTS AND ANALYSIS`** (~1600 words). `## 7.1 Summary of Results` (features delivered,
objectives met), `## 7.2 Comparative Analysis of Methodology` with `#### 7.2.1 Linear Regression vs Decision
Tree` (render a comparison `[[TABLE Table 7.1 — Linear Regression vs Decision Tree (CART).]]` using Table 6.1
numbers + working principle, pros/cons, when-to-use; evidence-based, no unsupported "best" claims),
`#### 7.2.2 Architectural Comparison` (server-rendered FastAPI+Jinja2 vs SPA alternative — trade-offs),
`## 7.3 Observations`.

**ch8.md → `# 8. CONCLUSION AND FUTURE WORK`** (~1100 words). `## 8.1 Conclusion`,
`## 8.2 Objectives Achieved`, `## 8.3 Major Contributions`, `## 8.4 Limitations` (from Section 4.7),
`## 8.5 Future Enhancements` (escape regex / CSRF / HTTPS secure cookie / real dataset & richer models /
map search / notifications / pagination on browse / rate limiting), `## 8.6 Final Remarks`.

Remember: full academic paragraphs, cite [n] where relevant, honesty about the synthetic dataset and the
modest R², and use placeholders (never invented facts) for any institutional detail.
