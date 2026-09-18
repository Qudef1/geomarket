## 1. Project Overview

GeoMarket AI is an intelligent geospatial decision-support system for evaluating business locations.

The system helps users answer questions such as:

> "Where should I open a coffee shop in Helsinki for students and office workers?"

The application analyzes geographic, infrastructure, demographic, competitive, and business-specific features and produces:

* location suitability scores;
* ranked candidate locations;
* interactive map visualizations;
* heatmaps;
* feature breakdowns;
* rule-based recommendations;
* ML-based predictions;
* human-readable explanations.

The project must be designed as a production-oriented portfolio project, not as a university-only prototype.

---

# 2. Core Product Flow

The main flow is:

1. User selects a city, area, or point on the map.
2. User selects a business type.
3. User optionally provides additional constraints:

   * budget;
   * target audience;
   * preferred area;
   * search radius;
   * custom requirements.
4. Backend creates candidate geographic locations.
5. Geospatial services collect raw geographic data.
6. Feature engineering converts raw geographic data into ML features.
7. Rule Engine evaluates explicit domain rules.
8. ML model predicts location suitability.
9. Decision Engine combines ML and rule-based results.
10. Explainability layer generates reasons behind the score.
11. API returns results.
12. Frontend displays:

* markers;
* candidate locations;
* heatmap;
* rankings;
* score breakdown;
* explanation.

---

# 3. High-Level Architecture

Use a modular monolith for the initial implementation.

Do NOT introduce microservices unless there is a demonstrated need.

Architecture:

```text
Frontend
   |
   v
FastAPI
   |
   +-----------------------+
   |                       |
   v                       v
Analysis Service       Search Service
   |
   +-------------------------------+
   |               |               |
   v               v               v
Geo Service    Feature Engine   Rule Engine
   |               |               |
   v               v               |
OSM/Overpass    PostGIS            |
                   |               |
                   +-------+-------+
                           |
                           v
                       ML Service
                           |
                           v
                    Decision Engine
                           |
                           v
                   Explainability
                           |
                           v
                         API
```

External data sources:

```text
OpenStreetMap
Overpass API
Nominatim
Optional:
Google Places
public demographic datasets
city open-data APIs
```

---

# 4. Technology Stack

## Backend

Primary language:

```text
Python 3.12+
```

Framework:

```text
FastAPI
Pydantic v2
SQLAlchemy 2
Alembic
```

Use asynchronous APIs where they provide real value, especially for network-bound external API calls.

Do not convert CPU-heavy ML/geospatial processing into async functions unnecessarily.

---

## Database

Use:

```text
PostgreSQL
PostGIS
```

PostGIS must be used for actual geospatial operations instead of implementing geographic queries manually in Python.

Examples:

* distance calculations;
* points inside polygons;
* radius searches;
* spatial intersections;
* nearest-neighbor queries.

---

## Cache

Use Redis for:

* caching external API responses;
* caching expensive feature computations;
* optional background-job state;
* rate-limit support.

External OSM data should not be fetched repeatedly when a valid cached response exists.

---

## Geospatial Data

Primary source:

```text
OpenStreetMap
Overpass API
```

Use OSM tags to extract POIs such as:

```text
amenity=cafe
amenity=restaurant
amenity=pharmacy
amenity=parking
amenity=university
highway=bus_stop
public_transport=*
shop=supermarket
office=*
railway=station
```

Do not scatter OSM tag definitions throughout the codebase.

Maintain centralized business/feature configuration.

Example:

```python
POI_CONFIG = {
    "cafe": {...},
    "restaurant": {...},
    "university": {...},
    "bus_stop": {...},
}
```

---

# 5. ML Architecture

ML must be isolated from HTTP/API code.

Expected pipeline:

```text
Raw geo data
    ↓
Feature Engineering
    ↓
Feature Vector
    ↓
ML Model
    ↓
ML Score
```

Initial models may include:

```text
Logistic Regression
Random Forest
XGBoost
LightGBM
```

Do not hard-code a specific model into business logic.

Define an abstraction such as:

```python
class LocationScoringModel:
    def predict(self, features: LocationFeatures) -> float:
        ...
```

Possible implementations:

```text
HeuristicScoringModel
RandomForestScoringModel
LightGBMScoringModel
```

This allows the system to operate before a high-quality labeled dataset exists.

---

# 6. Baseline Before ML

The project MUST have a deterministic scoring baseline before introducing trained ML.

Example:

```text
transport_score       0.20
target_audience_score 0.25
competition_score     0.15
poi_score             0.15
centrality_score      0.10
commercial_score      0.15
```

Then:

```text
baseline_score =
    Σ(weight_i * normalized_feature_i)
```

The baseline provides:

* a working MVP;
* a comparison point for ML;
* easier debugging;
* interpretable results;
* fallback when a trained model is unavailable.

---

# 7. Rule Engine

Rule Engine must be independent from ML.

Example:

```text
IF business_type = coffee_shop
AND universities_1000m >= 2
THEN score_modifier += 0.10
```

Another example:

```text
IF competitors_500m > threshold
AND target_population_score < threshold
THEN score_modifier -= 0.15
```

Rules must not be buried in API handlers.

Use domain structures similar to:

```python
class Rule:
    condition: ...
    effect: ...
    explanation: ...
```

Each triggered rule should be traceable.

The API should be able to return:

```json
{
  "rule": "coffee_near_university",
  "effect": 0.1,
  "reason": "Two universities are located within 1 km."
}
```

---

# 8. Decision Engine

The final score should be calculated in one dedicated component.

Conceptually:

```text
Final Score =
    ML Score
    + Rule Modifiers
    + Constraint Adjustments
```

The exact combination may evolve.

Do not calculate final scores in routers/controllers.

Decision Engine must return structured information:

```json
{
  "score": 0.87,
  "ml_score": 0.81,
  "rule_adjustment": 0.06,
  "confidence": 0.78,
  "features": {},
  "reasons": []
}
```

Scores must be normalized to a documented range, preferably:

```text
0.0 — 1.0
```

The UI may convert this to:

```text
0 — 100
```

or:

```text
0 — 10
```

---

# 9. Explainability

Every recommendation must be explainable.

Do not return only:

```json
{"score": 0.87}
```

Return a breakdown.

Example:

```json
{
  "score": 0.87,
  "positive_factors": [
    "Excellent public transport availability",
    "High concentration of offices",
    "University located within 700 m"
  ],
  "negative_factors": [
    "High number of competing coffee shops"
  ]
}
```

For tree-based ML models, later iterations may use SHAP.

LLMs must NOT invent explanations for numerical model predictions.

If an LLM is introduced, it may verbalize structured evidence generated by the Decision Engine, but the factual evidence must originate from deterministic system components.

---

# 10. Feature Engineering

Feature engineering must be its own module.

Example features:

```text
cafes_250m
cafes_500m
cafes_1000m

restaurants_500m

universities_500m
universities_1000m

bus_stops_250m
bus_stops_500m

metro_stations_1000m

offices_500m
offices_1000m

parking_500m

supermarkets_1000m

distance_to_center

poi_density_500m

competitor_density

transport_accessibility

target_audience_proxy
```

Never mix raw external API response schemas with ML features.

Use the pipeline:

```text
External API response
        ↓
Domain objects
        ↓
Feature extraction
        ↓
LocationFeatures
        ↓
ML
```

---

# 11. Geographic Radii

Default analysis radii:

```text
250 m
500 m
1000 m
```

Radii must be configurable.

Do not hard-code radius values throughout the codebase.

---

# 12. Candidate Generation

The system should support two analysis modes.

## Point Analysis

User selects one point.

The system evaluates that point.

## Area Analysis

User selects:

```text
city
district
bounding box
polygon
```

Candidate points are generated across the area.

Initial implementation may use a regular grid.

Example:

```text
250–500 meter spacing
```

Each grid point is evaluated independently.

The results are used for:

```text
heatmap
ranking
top-N recommendations
```

Candidate generation must be separated from candidate scoring.

---

# 13. Data Models

Important domain entities should include:

```text
BusinessType
Location
CandidateLocation
AnalysisRequest
GeoFeature
LocationFeatures
RuleResult
ModelPrediction
LocationScore
AnalysisResult
```

Persistence entities may include:

```text
User
Analysis
Candidate
FeatureSnapshot
Prediction
```

Keep domain models separate from ORM models where useful.

---

# 14. Suggested Repository Structure

```text
geomarket-ai/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── dependencies/
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── domain/
│   │   │   ├── models/
│   │   │   └── enums/
│   │   │
│   │   ├── services/
│   │   │   ├── analysis/
│   │   │   ├── geo/
│   │   │   ├── features/
│   │   │   ├── rules/
│   │   │   ├── scoring/
│   │   │   └── explainability/
│   │   │
│   │   ├── integrations/
│   │   │   ├── osm/
│   │   │   ├── overpass/
│   │   │   └── geocoding/
│   │   │
│   │   ├── ml/
│   │   │   ├── models/
│   │   │   ├── training/
│   │   │   ├── inference/
│   │   │   └── evaluation/
│   │   │
│   │   ├── db/
│   │   │   ├── models/
│   │   │   ├── repositories/
│   │   │   └── migrations/
│   │   │
│   │   └── main.py
│   │
│   └── tests/
│
├── frontend/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── samples/
│
├── notebooks/
│
├── models/
│
├── scripts/
│
├── docker/
│
├── docs/
│
├── docker-compose.yml
├── AGENTS.md
├── PLAN.md
├── README.md
└── .env.example
```

Avoid placing production ML logic exclusively inside notebooks.

Notebooks are for:

* exploration;
* visualization;
* experiments;
* dataset investigation.

Reusable code belongs in `backend/app/ml`.

---

# 15. API Design

Use REST initially.

Suggested endpoints:

```text
GET  /health

POST /api/v1/analysis/point
POST /api/v1/analysis/area

GET  /api/v1/analysis/{analysis_id}

GET  /api/v1/analysis/{analysis_id}/candidates

GET  /api/v1/business-types

GET  /api/v1/geo/search
```

Example point request:

```json
{
  "business_type": "coffee_shop",
  "latitude": 60.1699,
  "longitude": 24.9384,
  "target_audience": [
    "students",
    "office_workers"
  ]
}
```

Example response:

```json
{
  "score": 0.87,
  "grade": "high",
  "features": {
    "competitors_500m": 7,
    "bus_stops_500m": 9,
    "universities_1000m": 2
  },
  "components": {
    "transport": 0.91,
    "competition": 0.63,
    "target_audience": 0.89
  },
  "reasons": []
}
```

Use typed Pydantic request and response schemas.

---

# 16. Frontend

Recommended stack:

```text
React
TypeScript
MapLibre GL JS
```

OpenStreetMap-compatible map tiles may be used.

Main UI:

```text
Map
+
Search
+
Business configuration panel
+
Analysis results panel
```

Map layers should eventually include:

```text
candidate markers
heatmap
selected location
analysis radius
POIs
district boundaries
```

Keep map visualization separate from scoring logic.

---

# 17. Background Processing

Single-point analysis may execute synchronously if latency is acceptable.

Large area analysis should eventually use background jobs.

Potential implementation:

```text
Celery / RQ / Arq
+
Redis
```

Do not introduce a task queue during the earliest MVP unless required.

---

# 18. Data Quality

External geographic data is imperfect.

The code must handle:

```text
missing tags
missing POIs
API timeouts
rate limiting
duplicated objects
invalid coordinates
partial external responses
```

Never silently replace missing data with arbitrary values.

Feature defaults must be explicit.

---

# 19. Testing Requirements

Tests are mandatory.

Use:

```text
pytest
pytest-asyncio
httpx
```

Tests should cover:

```text
feature extraction
rule evaluation
score calculation
candidate generation
coordinate validation
API schemas
external API adapters
cache behavior
```

External APIs must be mocked in unit tests.

Tests must not depend on the availability of Overpass API.

---

# 20. Code Quality

Use:

```text
ruff
mypy
pre-commit
```

All public service boundaries should have type annotations.

Prefer small, testable functions.

Avoid:

```text
god classes
huge API handlers
global mutable state
business logic in routers
SQL inside route handlers
ML inference inside controllers
```

---

# 21. Configuration

Configuration must come from environment variables.

Use Pydantic Settings.

Example:

```text
DATABASE_URL
REDIS_URL
OVERPASS_URL
NOMINATIM_URL
MODEL_PATH
LOG_LEVEL
```

Never commit secrets.

Maintain:

```text
.env.example
```

---

# 22. Docker

The project should run locally with:

```bash
docker compose up
```

Expected services:

```text
backend
frontend
postgres
redis
```

PostgreSQL image must include PostGIS.

---

# 23. Observability

Use structured logging.

Important operations should log:

```text
analysis_id
candidate_id
external API latency
feature extraction latency
ML inference latency
number of candidates
cache hit/miss
```

Do not log secrets or unnecessary personal data.

---

# 24. Performance

Avoid performing one external API request for every individual feature.

Prefer batching geographic queries.

Cache geographically reusable data.

For area analysis, avoid:

```text
N candidates × N feature API calls
```

Prefer:

```text
fetch area once
        ↓
store/process POIs
        ↓
calculate features locally
```

This is an important architectural requirement.

---

# 25. ML Evaluation

Never claim the ML model is better simply because it produces plausible scores.

Every trained model must have documented evaluation.

Depending on formulation, track metrics such as:

```text
ROC-AUC
F1
Precision
Recall
MAE
RMSE
NDCG
MAP
Precision@K
```

Ranking metrics are preferred once the task becomes location ranking.

Always compare trained models against the deterministic baseline.

---

# 26. Dataset Integrity

Prevent geographic data leakage.

Random train/test splitting can be misleading for spatial datasets because nearby points may be highly correlated.

Prefer geographic or temporal validation where appropriate.

Examples:

```text
train → several districts
test  → unseen district
```

or:

```text
train → several cities
test  → unseen city
```

Document dataset provenance.

---

# 27. Security

Validate:

```text
coordinates
radius
polygon size
number of candidates
business type
request size
```

Prevent users from triggering arbitrarily expensive geographic queries.

Apply sensible upper limits.

External URLs must come from trusted configuration rather than arbitrary user input.

---

# 28. Development Rules for Codex

When modifying the repository:

1. Inspect existing architecture before adding files.
2. Reuse existing abstractions where appropriate.
3. Do not duplicate functionality.
4. Do not introduce dependencies without a concrete reason.
5. Keep API, domain, persistence, external integrations, and ML concerns separated.
6. Add or update tests for meaningful behavioral changes.
7. Do not silently change API contracts.
8. Keep migrations compatible with the current database state.
9. Prefer incremental changes over large rewrites.
10. Run relevant tests after changes.
11. Run linting/type checking when practical.
12. Document important architectural decisions.
13. Do not fabricate datasets, benchmark results, model metrics, or external API capabilities.
14. Preserve reproducibility of ML experiments.
15. Never commit credentials or `.env` files.

---

# 29. Definition of Done

A feature is complete when:

```text
implementation exists
+
tests exist
+
types are valid
+
errors are handled
+
API contract is documented
+
relevant documentation is updated
```

For ML features additionally require:

```text
evaluation exists
+
baseline comparison exists
+
model artifact is versioned
+
feature schema is documented
```

---

# 30. Product Principle

GeoMarket AI is a decision-support system.

The goal is not to produce arbitrary AI-generated recommendations.

Every location score should ultimately be traceable to:

```text
geographic evidence
+
derived features
+
explicit rules
+
model output
```

The architecture should preserve that traceability throughout the project.
