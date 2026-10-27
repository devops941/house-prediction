# 3. SYSTEM ANALYSIS

## 3.1 Existing System Methodology

The conventional property market in India operates through a network of intermediaries — brokers, sub-brokers, and real-estate agents — who act as the primary conduit between property owners and prospective buyers or tenants. A seller or landlord typically engages a registered broker who lists the property on commercial portals such as 99acres [13], Magicbricks [14], or NoBroker [12]. The broker controls which details are disclosed, at what price, and to which parties, creating significant information asymmetry. Buyers and tenants are therefore dependent on the broker's availability, honesty, and access to complete information.

The financial cost of this intermediation is substantial. For sale transactions, brokers typically charge one to two percent of the transaction value — on a ₹50 lakh property, that is ₹50,000–₹1,00,000 at closing. For rentals, the convention is one month's rent paid upfront as brokerage. These fees are in addition to any portal subscription or featured-listing charges, meaning both parties bear an indirect cost that contributes nothing to the intrinsic value of the transaction.

Pricing transparency is a further weakness. Because valuations are negotiated privately, there is no objective reference point against which a buyer can verify whether an asking price is fair. Valuation tools on large portals are either locked behind premium tiers or based on aggregated indices that miss granular locality-level variation. First-time buyers are especially disadvantaged, and many deals close at prices materially above what a data-informed estimate would suggest.

The overall workflow of the existing broker-mediated process is depicted in Figure 3.1. A property owner contacts a broker, who photographs and lists the property on a commercial portal. Buyers search those portals, contact the broker, and await arranged viewings. Negotiations are conducted through the broker, and the deal closes only after the commission is settled — each step introducing delay, opacity, and cost.

[[FIG fig3_1_existing.png | Figure 3.1 — Workflow of the existing broker-mediated process.]]

Figure 3.1 illustrates how the broker acts as a mandatory node at every stage — initial listing, enquiry handling, price negotiation, and deal closure. The shaded intermediary layer marks points where information can be withheld or distorted, forming the structural bottleneck that NestQuest is designed to eliminate.

## 3.2 Proposed System Architecture

NestQuest replaces the broker-mediated workflow with a self-service, owner-to-buyer platform built on a modern asynchronous web stack. The backend is implemented in **FastAPI** running on **Uvicorn** (ASGI) with **Python 3.12**, providing non-blocking request handling [1]. The data store is **MongoDB Atlas** accessed through the **Motor** async driver [9]. Property images are persisted on **Cloudinary**, decoupling media storage and delivery from the application server [11]. Authentication uses **bcrypt** password hashing at cost factor 12 [6] combined with **JWT** tokens [7] stored in httpOnly cookies, providing session security without a server-side session store.

From the user's perspective, the proposed workflow is significantly simpler. An owner registers, completes a listing form — including up to fifteen images uploaded directly to Cloudinary — and submits for administrator review. Once approved, the listing becomes publicly visible and searchable. Buyers browse using rich filters (listing type, property type, city, locality, price range, area, bedrooms, furnishing status), view individual property pages, and send enquiries directly to the owner. No broker is involved at any point.

The AI price estimator, implemented in **scikit-learn** [2] as a Linear Regression model trained on a synthetic dataset of 545 rows, is available to all authenticated users from the Insights page. A user supplies twelve property attributes — area, bedrooms, bathrooms, stories, and seven binary amenity flags — and receives an instant price estimate with a confidence range of ±max(8% of the estimate, model RMSE). This addresses pricing opacity, though users should treat results as a guide rather than a formal valuation given the synthetic training data and an R² of approximately 0.65 [2][3].

The proposed workflow is illustrated in Figure 3.2, which shows four actor lanes — Owner, Platform (NestQuest), Administrator, and Buyer/Tenant — with direct horizontal interactions between Owner and Buyer/Tenant facilitated by the platform, bypassing any broker layer entirely.

[[FIG fig3_2_proposed.png | Figure 3.2 — Workflow of the proposed NestQuest system.]]

Figure 3.2 demonstrates the elimination of the intermediary layer relative to Figure 3.1. The owner creates and manages listings directly on the platform; the administrator approves or rejects submissions through a dedicated panel; and the buyer interacts with listing content and the AI estimator before sending an enquiry that reaches the owner's inbox without broker involvement. The platform's role is facilitation rather than gatekeeping — the defining architectural distinction of the proposed system.

## 3.3 Advantages of the Proposed System

NestQuest offers measurable advantages across every dimension of the property search process. Table 3.1 presents a structured comparison of the existing broker-mediated portal approach and the NestQuest approach across seven key aspects.

[[TABLE Table 3.1 — Existing vs proposed system.]]
| Aspect | Existing (broker-led portals) | Proposed (NestQuest) |
|---|---|---|
| Intermediary | Broker / agent | None — owner to buyer direct |
| Brokerage cost | 1–2% of sale / 1 month rent | Zero |
| Pricing transparency | Opaque, negotiated | AI fair-price estimate + listed price |
| Posting | Often paid / broker-gated | Free self-service |
| Moderation | Minimal | Admin approval + featured flags |
| Data ownership | Portal/broker | Platform + verified owners |
| Access | Business hours | 24×7 web self-service |

Table 3.1 encapsulates the core value proposition of NestQuest. The elimination of brokerage cost is the most tangible benefit: a buyer seeking a flat at ₹30,000/month saves ₹30,000 in upfront brokerage. The AI estimator addresses pricing opacity by providing an independent reference before negotiating. Free self-service posting lowers the barrier for small landlords who lack a broker relationship. Administrator moderation — requiring explicit approval before a listing becomes visible — provides quality control largely absent from broker-led portals, where listings are often stale or duplicated. And 24×7 availability removes dependence on broker working hours.

The platform also improves data ownership. In the existing model, property data resides with the broker and portal, creating lock-in that disadvantages owners. In NestQuest, owners register directly, retain full control, and can edit or withdraw listings at any time. The `verified` flag applied on admin approval gives buyers a quality signal absent in broker-gated portals, representing a shift from a broker-centric to an owner-centric market model.

## 3.4 Feasibility Study

The following subsections examine technical, economic, and operational feasibility. The study concludes that NestQuest is technically achievable with freely available open-source components, economically viable at very low cost using managed free-tier cloud services, and operationally sustainable by a small team or individual developer.

#### 3.4.1 Technical Feasibility

The entire technology stack is composed of mature, well-documented open-source libraries and managed cloud services. **FastAPI** provides automatic OpenAPI documentation, Pydantic v2 data validation [16], and native async/await support, making it suitable for a marketplace with concurrent user sessions [1]. **MongoDB Atlas** offers a free M0 cluster (512 MB, shared compute) adequate for a demonstration and early-production workload of a few hundred listings [9]. **Motor** integrates cleanly with FastAPI's event loop. **scikit-learn** [2] provides the Linear Regression model and feature pipeline, relying only on standard numpy arrays and pandas DataFrames [4][5] listed in `requirements.txt`. **Cloudinary** offers a free tier with 25 GB storage and 25 GB monthly bandwidth, sufficient for dozens to a few hundred listings [11].

No special hardware is required: a standard machine with 4 GB RAM and Python 3.12 runs the full stack locally. The project runs on Windows 11 with a single `python run.py` command launching Uvicorn on port 8000. Deployment to a Linux VPS requires only Python, `pip`, and the environment variables in `.env`. The custom `decision_tree.py` exists solely to work around a Windows Application Control (WDAC) policy that blocked scikit-learn's compiled tree extension during training; it is not loaded at runtime. There are no proprietary tools, licensed software, or specialised hardware dependencies, making technical risk very low.

#### 3.4.2 Economic Feasibility

Economic feasibility assesses the cost of building and operating the system against the benefits it delivers. Table 3.2 presents an indicative cost estimate for developing and hosting NestQuest. All figures are **estimates and assumptions** based on publicly advertised pricing at the time of writing; actual costs should be verified before deployment.

[[TABLE Table 3.2 — Indicative cost estimate (all figures are ESTIMATES/assumptions).]]
| Item | Tier / Assumption | Estimated Cost |
|---|---|---|
| MongoDB Atlas database | Free M0 shared cluster (512 MB) — ESTIMATE | ₹0 / month |
| Cloudinary image hosting | Free tier (25 GB storage, 25 GB bandwidth) — ESTIMATE | ₹0 / month |
| VPS hosting (e.g., DigitalOcean, Hetzner, or Indian providers) | Shared/entry VPS with 1 vCPU, 1–2 GB RAM — ESTIMATE | ₹400–800 / month |
| Domain name (e.g., .in or .com TLD) | Annual registration — ESTIMATE | ₹900 / year (~₹75 / month) |
| SMTP email service | Free tier (e.g., Gmail SMTP with app password) — ESTIMATE | ₹0 / month |
| SSL/TLS certificate | Let's Encrypt automated — ESTIMATE | ₹0 |
| Developer time — initial build | [TO BE FILLED: actual hours logged]; assumed ~200–300 hrs @ ₹0 (academic project) | ₹0 (academic) |
| Developer time — ongoing maintenance | ~4–8 hrs/month for updates and monitoring — ESTIMATE | ₹0 (academic) or market rate |
| **Estimated total running cost** | — | **~₹475–875 / month** |

Table 3.2 shows recurring operational costs of approximately ₹475–₹875 per month, as primary cloud services (database and image hosting) use permanent free tiers adequate for an academic or early-stage deployment. The dominant variable cost is VPS hosting. At scale, upgrades to a paid Atlas tier and higher-capacity VPS would be needed, but costs remain proportional to platform value. Since brokerage savings on a single transaction (₹30,000 or more) exceed the platform's estimated annual running cost, the economic case is strongly positive. If commercialised, the initial build cost could be amortised against a premium featured-listing subscription or a thin facilitation fee well below current broker rates.

#### 3.4.3 Operational Feasibility

NestQuest is designed to be operated by a small administrative team — potentially a single administrator — via a built-in web-based admin panel at `/admin`. The panel provides aggregate statistics (total users, listings, pending approvals, enquiries), a property moderation queue, user management with role promotion and account deletion, and a predicted-price log. No command-line access or database expertise is required for routine operations.

The application boots with a single `python run.py` command that launches Uvicorn, establishes the database connection, creates required indexes idempotently, seeds the admin account from environment variables, and optionally pre-populates twenty demonstration listings via `SEED_DEMO_DATA=true`. A new deployment can be established in under ten minutes given a configured `.env` file and a running Atlas cluster.

The interface is entirely web-based, requiring only a modern browser. Server-rendered Jinja2 templating ensures pages render correctly even with JavaScript disabled. The platform is available 24×7; enquiries are persisted in the database and optionally delivered by email (SMTP), ensuring owners are notified regardless of when a buyer submits. No specialised operator training, proprietary runtime infrastructure, or paid third-party services are needed for normal operation, making operational risk low.
