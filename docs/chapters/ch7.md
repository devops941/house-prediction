# 7. RESULTS AND ANALYSIS

## 7.1 Summary of Results

NestQuest delivers a brokerage-free property marketplace augmented by an AI price estimator. Owners post listings at no cost, buyers and tenants search and enquire directly, and an instant fair-price guide is available at the point of decision.

The authentication module provides secure registration and login via `bcrypt` password hashing (cost factor 12) and JWT tokens in an httpOnly cookie [6][7]. The listings module supports the full lifecycle from draft through admin moderation to publication, with rich filters (listing type, property type, city, locality, price, area, bedrooms, furnishing) and five sort orders. Enquiry and shortlist modules let registered users contact owners and save favourites, eliminating the broker intermediary. The admin panel handles approval, rejection, featured flags, and user management — together delivering a complete end-to-end marketplace workflow.

The AI price estimator is trained on a synthetic dataset of 545 rows, split 80/20 (436 training, 109 test). Linear Regression was selected on the basis of its superior R² of 0.6538 on the held-out test set; the custom CART Decision Tree achieved only R² 0.4138 on the same split. The estimator is integrated via `/api/ml/predict`, returning a predicted price with a ± range and logging each prediction to the `predictions` collection. R²≈0.65 is modest — sufficient for a fair-price guide but not a professional valuation — a limitation attributable in part to the synthetic, linearly-generated training data [2][3].

Server-side Jinja2 rendering produces near-instant page loads with no JavaScript build pipeline, MongoDB Atlas indexes keep query latency low, and Cloudinary delivers reliable image hosting. All eight primary and secondary objectives from Chapter 1 are addressed at a level appropriate to a final-year academic project, with gaps documented in the limitations.

## 7.2 Comparative Analysis of Methodology

### 7.2.1 Linear Regression vs Decision Tree

The training pipeline evaluated two algorithms on the same synthetic dataset: scikit-learn `LinearRegression` and a from-scratch CART regression tree (`decision_tree.py`, max depth 5, min samples to split 10) [2][3]. The custom CART was necessitated by an Application Control policy that blocked scikit-learn's compiled tree extension at training time; it serves only as a baseline and is not loaded at runtime. Table 7.1 compares both approaches across empirical metrics, working principles, advantages, disadvantages, and appropriate use conditions.

[[TABLE Table 7.1 — Linear Regression vs Decision Tree (CART).]]
| Criterion | Linear Regression (selected) | Decision Tree — CART (baseline) |
|---|---|---|
| **R² (test set, n=109)** | 0.6538 | 0.4138 |
| **MAE (test set)** | ₹7,58,066 | ₹9,63,666 |
| **RMSE (test set)** | ₹9,39,058 | ₹12,21,894 |
| **Working principle** | Fits a hyperplane y = β₀ + β₁x₁ + … + βₙxₙ by minimising the sum of squared residuals (OLS). Predicts by evaluating the learned weight vector against the input feature vector. | Recursively partitions the feature space into axis-aligned rectangles by greedily minimising SSE at each split. Predicts the mean target value of training samples in the leaf reached by a query instance. |
| **Assumptions** | Linearity between features and target; independence of errors; homoscedasticity. | No distributional assumptions; handles non-linear boundaries and feature interactions naturally. |
| **Advantages** | Computationally trivial to train and predict; highly interpretable (coefficients show direction and magnitude of feature influence); low variance on small datasets; works well when the true relationship is approximately linear. | Can capture non-linear relationships and feature interactions without manual engineering; no scaling required; can fit complex patterns on larger datasets. |
| **Disadvantages** | Cannot model non-linear relationships without explicit feature engineering; sensitive to outliers via squared-error criterion; coefficient reliability degrades when features are correlated. | Prone to high variance and overfitting on small datasets (545 rows here); axis-aligned splits cannot represent diagonal boundaries; performance degrades without sufficient training data relative to tree depth. |
| **Why underperformed on this dataset** | — (performed better) | The 545-row dataset is too small for a depth-5 tree to generalise well; high variance causes poor test-set R² despite potentially lower training error. |
| **When to use** | Appropriate when the feature–target relationship is approximately linear, the dataset is small-to-medium, and interpretability is required. Also correct when the generating process is itself linear — as it is here. | Appropriate when the dataset is large, the relationship is non-linear or includes threshold effects, and some loss of interpretability is acceptable. |

Linear Regression outperforms the CART baseline across all three metrics: R² improves by 0.24 points (0.4138 → 0.6538), MAE falls by ₹2,05,600, and RMSE by ₹2,82,836. This is consistent with the data's provenance — the dataset was generated by a fixed linear formula with additive Gaussian noise, so the data-generating process is itself linear [2][3]. This result should not be generalised: real-world property datasets typically exhibit non-linear interactions that tree-based models capture effectively. The selection of Linear Regression is justified specifically for this synthetic dataset.

### 7.2.2 Architectural Comparison

NestQuest employs a **server-rendered architecture**: a FastAPI application (ASGI, Uvicorn) renders Jinja2 HTML templates on every request and delivers complete pages to the browser [1][10]. This contrasts with the **Single-Page Application (SPA)** pattern, in which a JavaScript framework runs in the browser and communicates with a JSON API.

Server rendering eliminates front-end build complexity — there is no bundler, no client-side routing library, no hydration overhead. The entire front-end is hand-written CSS (~460 lines) and vanilla JavaScript (~450 lines). It also produces fully formed HTML that is inherently more accessible to search engines and screen readers, and Jinja2 integrates tightly with the Python backend, allowing session state and role-based conditionals to be injected into templates without a separate serialisation layer.

The trade-off is a full HTTP round trip for most user interactions, whereas an SPA updates UI components without reloading the document. NestQuest partially mitigates this through a `fetch`-based layer in `app.js` for the shortlist toggle, AI estimator form, and image uploads; browse and search pages still require a server round trip. Session state is carried in a cookie-validated JWT rather than in-process memory, making the application stateless and horizontally scalable without sticky sessions.

The server-rendered FastAPI + Jinja2 architecture suits the access patterns of a property marketplace (read-heavy browsing with discrete writes), keeps technical scope achievable within the project timeline, and delivers acceptable page-load performance. A SPA would be preferable if the scope were extended to real-time features such as live price-trend charts, map overlays, or instant messaging.

## 7.3 Observations

The R² of 0.6538 reflects the estimator's ability to recover a known linear function, not to generalise to real Indian property data. The model is useful as a demonstration of the ML integration pipeline and as a fair-price guide within the platform's context, but its predictions should not be interpreted as market valuations. Future work should replace the synthetic dataset with a real, curated dataset of Indian property transactions.

The thirteen encoded features capture structural property attributes but omit the variables most strongly correlated with real-world price variation: location specificity, construction age relative to locality average, and recent comparable sales. The correlation heatmap (Figure 6.4) shows area and bedroom count as the strongest numeric predictors within the current feature set. Richer feature engineering or geospatial signals would likely produce a materially higher R² on real-world data.

The custom CART implementation, while a useful exercise in greedy SSE-minimisation, performed markedly worse than scikit-learn Linear Regression. The depth-5 constraint limits expressive capacity, and 545 rows are insufficient for reliable generalisation at that depth. On a larger, genuinely non-linear dataset, a properly tuned ensemble (Random Forest or Gradient Boosting) would be a far more competitive baseline than a single shallow tree [3].

Architecturally, logging every prediction to the `predictions` MongoDB collection creates a valuable audit trail. The distribution of user-submitted feature combinations in this collection can reveal which property configurations are most frequently queried, providing data-driven guidance for future model retraining — a simple design decision that demonstrates how a production ML system can gather operational feedback before active retraining infrastructure is built.

Finally, the project demonstrates that a functional, multi-role, database-backed marketplace with an embedded ML estimator can be built and deployed on a minimal infrastructure footprint — MongoDB Atlas free tier, Cloudinary free tier, and a modest virtual private server — making the NestQuest model practically replicable for small-scale, community-level property markets where broker fees create a meaningful economic burden.
