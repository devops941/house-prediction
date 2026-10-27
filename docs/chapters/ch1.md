# 1. INTRODUCTION

## 1.1 Overview of the Project

NestQuest is a brokerage-free, server-rendered property marketplace developed as a final-year undergraduate project at [College Name], [Academic Year]. Property owners publish residential and commercial listings at no cost; prospective buyers or tenants discover, shortlist, and contact owners directly without any intermediary. The system is built on **FastAPI** / Uvicorn (ASGI), **Jinja2** server-rendered templates, and **MongoDB Atlas**, with authentication secured by bcrypt and JSON Web Tokens. An embedded scikit-learn Linear Regression model provides users with an instant AI-driven price estimate — a transparent fair-price guide at the point of interest.

The motivation is the persistent structural inefficiency of the Indian residential property market, where brokers extract fees of one to two per cent of sale value or one month's rent. NestQuest delivers a self-service digital channel that gives owners direct reach to buyers and seekers access to transparent price data, while demonstrating how a data-driven feature can be integrated responsibly — with honest disclosure of its limitations — within a conventional marketplace interface.

## 1.2 Background of the Study

The Indian real-estate sector is a major GDP contributor, yet property transactions remain heavily dependent on personal intermediaries. Large-scale portals such as 99acres [13] and Magicbricks [14] digitised listing catalogues from the early 2000s but reinforced the intermediary model by monetising broker subscriptions. NoBroker [12] departed by positioning itself as a brokerage-free channel, demonstrating consumer demand for owner-direct contact. Globally, Zillow [15] combined listing aggregation with an automated valuation model (AVM) — the Zestimate — setting an industry precedent for embedding price intelligence within property search.

Open-source libraries such as scikit-learn [2], pandas, and NumPy have lowered the barrier to building AVMs considerably, enabling individual developers to train, evaluate, and deploy regression models as microservices. The remaining challenge is integration: connecting the ML inference layer to the user interface in a way that communicates statistical uncertainty to a non-technical audience. NestQuest addresses this by embedding a clearly labelled price-guide feature with honest disclosure that the model achieves R² ≈ 0.65 on a synthetic dataset and constitutes a guide rather than a professional valuation. The codebase began as a single-purpose Flask application for house price prediction, then was rebuilt into the NestQuest FastAPI marketplace retaining the trained model — illustrating the common pattern where proof-of-concept ML work is incrementally incorporated into a larger product.

## 1.3 Problem Statement

Property search in India is dominated by broker-subscribed portals, creating three interconnected problems. First, **pricing opacity**: listed prices are often inflated as an opening negotiating position, and seekers have no independent reference to evaluate fairness. Second, **direct cost burden**: brokerage fees of one to two per cent of sale value or one month's rent fall disproportionately on less affluent seekers with no alternative channel. Third, **information asymmetry**: broker-controlled listings may suppress contact details, delay responses, or obscure the actual owner's identity, impeding due diligence.

Current Indian portals provide little or no data-driven price guidance; seekers must engage a valuation professional, consult disconnected price-index reports, or rely on broker hearsay. An embedded AI estimator adds measurable value by anchoring expectations with a quantitative reference derived from observable features such as area, bedroom count, and furnishing status — a user-experience gap this project directly addresses.

## 1.4 Existing System

The current landscape of online property platforms falls into three archetypes: the broker-subscription portal (99acres [13] and Magicbricks [14]), the brokerage-free owner-direct model (NoBroker [12]), and the AVM-integrated marketplace (Zillow [15]). Each addresses some of the identified problems but none resolves all three simultaneously within a single, freely accessible platform for the Indian context.

99acres and Magicbricks hold large listing inventories but derive significant revenue from broker subscriptions and premium placement fees, so the majority of listings are intermediated. NoBroker disrupted this model by forbidding broker listings, proving the commercial viability of owner-direct transactions; however, it does not provide an AI price estimator. Zillow [15] offers the most sophisticated price-intelligence layer through the Zestimate, using proprietary hedonic regression and neural-network models trained on millions of American properties, but it is geographically limited to the United States. NestQuest adopts the owner-direct philosophy of NoBroker, the catalogue-and-search interface of 99acres and Magicbricks, and the price-intelligence concept of Zillow's Zestimate, while addressing each platform's primary limitation within a unified application.

Table 1.1 below summarises the key differences between existing broker-mediated portals and the proposed NestQuest system across six critical dimensions.

[[TABLE Table 1.1 — Existing portals vs NestQuest.]]
| Aspect | Existing (broker-led portals) | Proposed (NestQuest) |
|---|---|---|
| Intermediary | Broker / agent | None — owner to buyer direct |
| Brokerage cost | 1–2% of sale / 1 month rent | Zero |
| Pricing transparency | Opaque, negotiated | AI fair-price estimate + listed price |
| Posting | Often paid / broker-gated | Free self-service |
| Moderation | Minimal | Admin approval + featured flags |
| Data ownership | Portal/broker | Platform + verified owners |
| Access | Business hours | 24×7 web self-service |

As Table 1.1 illustrates, the most significant structural differentiators are the complete elimination of brokerage cost, the provision of an AI-generated fair-price estimate at the point of listing and search, and a free self-service posting workflow. The admin-moderated approval queue addresses the quality and trust deficit of open platforms by ensuring listings are reviewed before becoming publicly visible.

## 1.5 Objectives of the Project

The primary objective of NestQuest is to design, develop, and deploy a brokerage-free property marketplace web application that directly connects property owners with buyers and tenants, augmented by an AI-driven price estimator that provides quantitative price guidance based on property features.

The following secondary objectives, each measurable against the delivered system, support the primary goal.

1. To implement a secure, role-based authentication system using bcrypt password hashing and JWT tokens, ensuring that owner, registered-user, and administrator roles receive appropriately scoped access to all platform functions.
2. To build a full property-listing lifecycle — including creation, image upload via Cloudinary, admin moderation, search and filtering, and soft-deletion with cascading removal of associated saved items and enquiries — within a single coherent application.
3. To provide a multi-attribute property search interface supporting filtering by listing type, property type, city, locality, price range, bedroom count, furnishing status, and area range, with multiple sort orders, enabling seekers to narrow a large catalogue to a relevant shortlist efficiently.
4. To integrate a machine-learning price estimator, trained on a synthetic dataset modelled on a public Kaggle housing dataset, that accepts thirteen encoded property features and returns a predicted price with a confidence range, while honestly communicating the model's limitations (R² ≈ 0.65) to users.
5. To implement an enquiry and shortlist system whereby registered users can save listings to a personal shortlist and send direct messages to property owners, with optional SMTP email notification on enquiry receipt and an owner reply workflow.
6. To deliver an administration dashboard providing real-time platform statistics, user management (including role assignment and cascading deletion), and property moderation (status transitions: pending → active / rejected, with featured and verified flags).
7. To ensure application security through bcrypt cost-factor-12 password hashing, httpOnly JWT cookies, Pydantic v2 input validation, and documented acknowledgement of known limitations such as unescaped regex search and the absence of CSRF tokens, as starting points for future hardening.
8. To produce a complete academic project report documenting the system's analysis, design, implementation, and evaluation in conformance with the requirements of [College Name], [Academic Year].

## 1.6 Scope of the Project

NestQuest is scoped as a full-stack web application deployable on any server environment supporting Python 3.12 with network access to MongoDB Atlas and the Cloudinary API. The platform covers three listing categories — sale, rental, and commercial — across ten property types, with listings carrying up to fifteen images and fifteen amenity tags. The user-facing scope includes a public browse-and-search experience accessible without registration, a registered-user workflow covering profile management, property posting, shortlisting, and enquiry, and an admin workflow covering moderation, user management, and a statistics overview.

The machine-learning scope is intentionally modest: the AI price estimator is trained on a synthetic dataset of 545 rows generated to mirror a publicly available Kaggle housing dataset, and should not be interpreted as real-world predictive power (R² ≈ 0.65). Extension to a real-market dataset, richer feature engineering, or more powerful model architectures such as gradient-boosted trees is noted as future work. The project does not implement payment processing, legal document generation, mortgage calculation, geographical map search, or a mobile-native application; these represent natural future extensions outside the current academic scope. The SMTP email service is implemented but disabled by default and is considered an optional operational enhancement rather than a core dependency.

The report is structured as follows: Chapter 2 presents a literature survey of related work; Chapter 3 analyses the existing system and feasibility; Chapter 4 details system design including architecture, data models, and API surface; Chapter 5 describes implementation with representative code excerpts; Chapter 6 presents results and model performance; Chapter 7 provides comparative analysis; and Chapter 8 concludes with achievements, limitations, and future directions.
