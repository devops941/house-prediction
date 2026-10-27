# 2. LITERATURE SURVEY

This chapter surveys academic and technical literature that informed NestQuest's design, reviews four existing property platforms, compares approaches in a structured table, identifies research gaps, and explains how the proposed system addresses them.

## 2.1 Review of Related Work

### 2.1.1 Machine Learning for Regression and Price Estimation

Pedregosa et al. [2] introduced scikit-learn, whose consistent API for training, evaluation, and serialisation via `joblib` makes it straightforward to compare algorithms and deploy a trained estimator [2].

Hastie, Tibshirani, and Friedman [3] provide the mathematical foundation for both NestQuest models. Their treatment of ordinary least-squares shows the linear model minimises the sum of squared residuals and yields an interpretable coefficient per feature — the primary reason it was selected as the deployed estimator [3]. Their CART account describes the greedy recursive-partitioning strategy that minimises within-node squared error and uses `max_depth` to control over-fitting [3]; the NestQuest training notebook implements a from-scratch CART tree (`decision_tree.py`, `max_depth=5`, `min_samples_split=10`) as a baseline comparison against the linear model [3].

### 2.1.2 Data Manipulation and Numerical Computing

McKinney [4] introduced the pandas `DataFrame`, which provides column-oriented operations for reading CSV files, mapping categorical values, and applying one-hot encoding — steps used in the NestQuest training pipeline to convert six binary yes/no columns and the three-level `furnishingstatus` variable into numeric form [4]. Harris et al. [5] documented NumPy, whose vectorised arithmetic underpins both pandas and scikit-learn; its seeded pseudo-random generator is exploited in the NestQuest dataset synthesis (seed 42) and demo-data seeding (seed 2024) [5].

### 2.1.3 Password Security and Authentication

Provos and Mazières [6] introduced the bcrypt adaptive hashing scheme, which applies a Blowfish-based key schedule iterated a configurable number of times via a cost factor. NestQuest adopts bcrypt with cost factor 12 (`bcrypt.gensalt(rounds=12)`), following [6]'s recommendation to choose a cost that is expensive enough to deter offline attacks without imposing unacceptable login latency.

Jones, Bradley, and Sakimura [7] defined the JSON Web Token (JWT) standard in RFC 7519. A JWT encodes a signed JSON payload — subject, issue time, and expiry — so the server can verify authenticity without a session store. NestQuest issues HS256-signed JWTs carrying the user identifier, role, and expiry (`JWT_EXPIRE_MINUTES=10080`), stored in an `httpOnly` cookie named `nestquest_token` and also accepted via an `Authorization: Bearer` header [7]. The `httpOnly` flag prevents client-side JavaScript from reading the token, mitigating cross-site scripting exposure as described by the OWASP Foundation [8].

The OWASP Top 10 — 2021 [8] catalogues critical web-application risks including broken access control (A01), cryptographic failures (A02), and injection (A03). NestQuest addresses several: bcrypt mitigates cryptographic weakness [6][8]; dependency-injection guards (`optional_user`, `current_user`, `admin_user`) enforce access control; and Pydantic v2 [16] validates all inbound request bodies, reducing injection surface. Residual risks — unescaped `$regex` patterns in search queries and absent CSRF tokens — are acknowledged as future work, consistent with [8].

### 2.1.4 Web Frameworks, Databases, and Templating

Ramírez [1] documents FastAPI, the ASGI-based Python framework used as the NestQuest backend; it couples type annotations with Pydantic validation for automatic request parsing and OpenAPI documentation, and its `lifespan` context manager handles database connection, index creation, and demo-data seeding at startup [1]. MongoDB Inc. [9] documents the document-oriented database whose flexible model stores heterogeneous property attributes (up to fifteen amenities, fifteen images, ten optional numeric fields) without a relational schema; compound and full-text indexes on the `properties` collection are created at startup via Motor's `create_index` API [9]. Ronacher [10] documents Jinja2, whose `{% block %}` and `{% include %}` directives support a `base.html` template providing consistent navigation, authentication-state injection, and cache-busting across all pages [10].

## 2.2 Review of Existing Platforms

### 2.2.1 NoBroker

NoBroker [12] is an Indian property marketplace that eliminates real-estate brokers, allowing owners to post listings and buyers or tenants to contact them directly. Identity verification and a subscription fee charged to tenants beyond a free tier replace per-transaction brokerage [12]. A key limitation is this contact paywall: while owners post for free, tenants must purchase a plan to unlock owner details, partially reintroducing a monetary barrier [12]. NoBroker does not publicly expose an ML price estimator integrated into the listing workflow.

### 2.2.2 99acres

Info Edge (India) Ltd. operates 99acres [13], one of India's largest property portals. It combines broker-submitted and owner-submitted listings, rich filtering, and a proprietary "PropWorth" price-insight tool available on some listings. Brokers pay for premium visibility and handle a significant share of enquiries, reintroducing the information asymmetry that a brokerage-free model seeks to avoid [13]. The commercial model aligns incentives with brokers rather than end-users.

### 2.2.3 Magicbricks

Magicbricks [14] follows a broadly similar model to 99acres: a mixed owner-and-broker listing database, subscription-based lead generation for agents, and tools such as price trend graphs and an EMI calculator. Locality-level price trends are derived from aggregated listing prices — descriptive statistics rather than predictive ML outputs [14]. There is no publicly documented machine learning model for per-property estimates, and broker participation remains a structural feature of the business model [14].

### 2.2.4 Zillow and the Zestimate

Zillow Group [15] operates in the United States and publishes methodology notes on its Zestimate, trained on hundreds of millions of historical sale records, public tax assessments, and user-submitted data [15]. The approach demonstrates the ceiling of ML price estimation with rich real-world data, but the Zestimate is opaque to users, and Zillow's iBuying operations have faced well-publicised difficulties, illustrating that even sophisticated models carry substantial uncertainty [15]. For NestQuest, the Zestimate is an existence proof that ML estimation can be embedded in a marketplace, while also underscoring the gap between a production-grade model and NestQuest's modest estimator (R²≈0.65 on a synthetic dataset).

## 2.3 Comparison of Approaches

Table 2.1 consolidates the salient characteristics of the reviewed platforms and technical approaches against the NestQuest design.

[[TABLE Table 2.1 — Comparison of reviewed platforms and technical approaches.]]
| Dimension | 99acres [13] | Magicbricks [14] | NoBroker [12] | Zillow [15] | NestQuest (proposed) |
|---|---|---|---|---|---|
| Market / geography | India | India | India | USA | India (prototype) |
| Broker involvement | High (core revenue) | High (core revenue) | None (owner-direct) | None (iBuying) | None (owner-direct) |
| Listing cost to owner | Free basic / paid featured | Free basic / paid featured | Free | Free / paid tiers | Free self-service |
| Listing moderation | Automated + manual | Automated + manual | Automated | Automated | Admin approval workflow |
| Price estimation tool | Descriptive trend data | Descriptive trend data | None documented | ML Zestimate (proprietary) | scikit-learn Linear Regression [2] |
| Training data | Real market data | Real market data | N/A | Large-scale real-world data [15] | Synthetic dataset (545 rows) |
| Published ML metrics | Not disclosed | Not disclosed | N/A | Median AE by market | R²=0.65, MAE≈₹7.6 L, RMSE≈₹9.4 L |
| Authentication | Username/password + OTP | Username/password + OTP | Username/password + OTP | OAuth + email | bcrypt [6] + JWT [7] httpOnly cookie |
| Database technology | Not disclosed | Not disclosed | Not disclosed | Not disclosed | MongoDB Atlas [9], Motor async |
| Backend framework | Proprietary / undisclosed | Proprietary / undisclosed | Proprietary / undisclosed | Java / Scala stack | FastAPI [1] + Jinja2 [10] |
| Open-source / academic | No | No | No | Partially documented | Yes — academic prototype |

NestQuest shares the brokerage-free direct-contact model with NoBroker [12] but adds an integrated ML price estimator, an explicit admin moderation workflow, and a fully documented open technology stack. Unlike Zillow [15], whose Zestimate is trained on large-scale real data, NestQuest's estimator uses a synthetic dataset [5] and carries commensurately modest accuracy — an acknowledged limitation rather than an oversight.

## 2.4 Research Gaps Identified

Several gaps emerge from the survey. First, Indian platforms such as 99acres [13] and Magicbricks [14] do not publish methodology or accuracy metrics for their price-insight tools, making it impossible for users to calibrate trust in platform valuations — a contrast to the reproducibility norms advocated by [2] and [3]. Second, NoBroker [12] eliminates broker fees but imposes a subscription paywall on tenants; no reviewed platform combines entirely free access with direct owner contact. Third, none of the Indian platforms offers a real-time per-property ML estimate at the point of listing creation; pricing information is either historical trend data or manually entered. Fourth, the security practices of Indian property portals are undocumented, with no evidence of OWASP-recommended controls [8] such as adaptive password hashing [6] or stateless token authentication [7]. Fifth, the academic ML literature (e.g. [2][3]) focuses on model accuracy in isolation, without integrating a trained model into a full-stack application serving both listers and seekers in a single cohesive platform.

## 2.5 How the Proposed System Addresses the Gaps

NestQuest closes each identified gap within the constraints of an academic prototype. The platform is entirely free: owners post at no cost and users contact owners without any paywall, eliminating both broker fees and NoBroker's subscription barrier [12]. A scikit-learn Linear Regression estimator [2] is surfaced at `/insights` and the `/api/ml/predict` endpoint; its metrics (R²=0.6538, MAE≈₹7.58 L, RMSE≈₹9.39 L on 109 test rows) are documented in `model/metrics.json` and reported openly, following the transparency norms of [2] and [3].

Security is addressed through bcrypt with cost factor 12 [6], HS256-signed JWTs in `httpOnly` cookies [7], and Pydantic v2 input validation [16], with residual risks noted per OWASP guidance [8]. FastAPI [1] and MongoDB [9] provide a fully documented, reproducible baseline. An admin moderation workflow — absent from all reviewed commercial platforms — ensures listings are human-reviewed before publication. Integrating the ML estimator, marketplace, and moderation layer in a single server-rendered application is the primary architectural contribution distinguishing NestQuest from both the academic ML literature and existing commercial platforms.

## 2.6 Summary

This chapter surveyed the academic foundations of NestQuest — regression theory [3], scikit-learn [2], pandas [4], NumPy [5], bcrypt [6], JWT [7], OWASP guidance [8], FastAPI [1], MongoDB [9], and Jinja2 [10] — alongside four existing property platforms [12][13][14][15]. Table 2.1 shows that commercial Indian platforms rely on broker-mediated revenue with opaque pricing tools, while Zillow [15] demonstrates ML valuation at scale in a data-rich market. Four principal gaps were identified: opaque pricing metrics, residual financial barriers to direct contact, absence of real-time ML estimates at listing creation, and undisclosed security practices. NestQuest addresses all four within the scope of an academic prototype, honestly acknowledging the limitations of a synthetic training dataset and a linear model with R²≈0.65. The next chapter analyses the existing and proposed systems in greater detail.
