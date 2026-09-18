# PLAN.md — GeoMarket AI Development Plan

# 1. Goal

Build a production-oriented MVP of GeoMarket AI capable of answering:

> How suitable is this location for a particular type of business?

and later:

> What are the best locations for this type of business within a selected city or area?

The project should demonstrate:

```text
Python Backend
Geospatial Engineering
PostGIS
External APIs
Data Engineering
Feature Engineering
Machine Learning
Ranking
Explainable AI
Decision Support Systems
Frontend Map Visualization
Docker
Testing
Production Architecture
```

---

# 2. Target MVP

The first complete MVP should support one business type:

```text
coffee_shop
```

and one initial city for development/testing, for example:

```text
Helsinki
```

The architecture must remain generic enough to support other cities and business types.

The user should be able to:

1. Open a map.
2. Search for a location.
3. Select a point.
4. Select `Coffee Shop`.
5. Start analysis.
6. See nearby POIs.
7. Receive a suitability score.
8. See score components.
9. Understand positive and negative factors.
10. Run an area analysis.
11. View a heatmap.
12. See top candidate locations.

---

# 3. Phase 0 — Repository Bootstrap

## Goal

Create a clean development environment.

## Tasks

Create repository structure:

```text
backend/
frontend/
data/
models/
notebooks/
scripts/
docs/
```

Configure:

```text
Python 3.12+
FastAPI
pytest
ruff
mypy
pre-commit
```

Create:

```text
docker-compose.yml
.env.example
README.md
AGENTS.md
PLAN.md
```

Docker services:

```text
PostgreSQL + PostGIS
Redis
Backend
```

Add health endpoint:

```text
GET /health
```

## Result

The project starts locally and:

```bash
docker compose up
```

brings up the required infrastructure.

---

# 4. Phase 1 — Geographic Foundation

## Goal

Build the geographic core before introducing ML.

## Tasks

Implement coordinate domain models:

```python
Location(
    latitude,
    longitude
)
```

Add validation.

Implement PostGIS integration.

Support:

```text
Point
Polygon
Bounding Box
Radius
```

Implement basic spatial operations:

```text
distance
within radius
inside polygon
nearest objects
```

## Result

The backend can reliably work with geographic objects.

---

# 5. Phase 2 — Geocoding

## Goal

Allow users to search for places.

## Tasks

Integrate a geocoder.

Initial provider:

```text
Nominatim
```

Implement:

```text
text → coordinates
```

Example:

```text
"Kamppi, Helsinki"
        ↓
lat/lon
```

Endpoint:

```text
GET /api/v1/geo/search?q=Kamppi
```

Add:

```text
timeouts
error handling
caching
rate-limit awareness
```

## Result

Frontend/backend can convert human-readable locations into coordinates.

---

# 6. Phase 3 — OpenStreetMap / Overpass Integration

## Goal

Retrieve geographic context around a point.

## Tasks

Create Overpass client.

Support configurable radii:

```text
250 m
500 m
1000 m
```

Retrieve:

```text
cafes
restaurants
universities
bus stops
railway/metro stations
offices
parking
supermarkets
```

Create normalized domain model:

```python
POI(
    id,
    category,
    latitude,
    longitude,
    tags
)
```

Do not expose raw Overpass structures to the rest of the application.

Add Redis caching.

## Result

For any location:

```text
lat/lon
```

the backend can retrieve structured surrounding POIs.

---

# 7. Phase 4 — Feature Engineering

## Goal

Convert geographic data into numerical features.

## Tasks

Implement:

```text
cafes_250m
cafes_500m
cafes_1000m

restaurants_500m

universities_500m
universities_1000m

bus_stops_250m
bus_stops_500m

offices_500m
offices_1000m

parking_500m

supermarkets_1000m

distance_to_center

poi_density_500m
```

Introduce:

```python
LocationFeatures
```

Example:

```json
{
  "cafes_500m": 12,
  "restaurants_500m": 28,
  "universities_1000m": 2,
  "bus_stops_500m": 17,
  "offices_1000m": 153,
  "parking_500m": 4,
  "supermarkets_1000m": 7,
  "distance_to_center": 2.8
}
```

Write unit tests.

## Result

```text
coordinates
    ↓
POIs
    ↓
feature vector
```

works independently of ML.

---

# 8. Phase 5 — Baseline Scoring Model

## Goal

Create a fully working intelligent scoring system without requiring training data.

## Tasks

Define score components:

```text
competition
transport
target audience
commercial activity
centrality
amenities
```

Normalize raw features.

Implement weighted scoring.

Example:

```python
score = (
    transport * 0.20
    + audience * 0.25
    + competition * 0.15
    + commercial_activity * 0.15
    + centrality * 0.10
    + amenities * 0.15
)
```

Weights must be configuration-driven.

Create:

```python
BaselineScoringModel
```

## Result

Any point can receive a deterministic:

```text
0.0–1.0
```

suitability score.

---

# 9. Phase 6 — Rule Engine

## Goal

Add explicit expert knowledge.

## Tasks

Create generic rule abstraction.

Implement initial coffee-shop rules.

Examples:

```text
universities nearby
office concentration
transport accessibility
competition saturation
distance from activity centers
```

Each rule returns:

```text
triggered
score modifier
reason
```

Example:

```json
{
  "rule": "university_proximity",
  "triggered": true,
  "modifier": 0.08,
  "reason": "Two universities are located within 1 km."
}
```

## Result

The project now contains both:

```text
quantitative scoring
+
symbolic expert rules
```

which makes it a hybrid intelligent information system.

---

# 10. Phase 7 — Decision Engine

## Goal

Centralize final decision logic.

## Tasks

Create:

```python
DecisionEngine
```

Inputs:

```text
LocationFeatures
Baseline/ML prediction
RuleResults
User constraints
```

Output:

```python
LocationScore
```

Example:

```json
{
  "score": 0.87,
  "base_score": 0.81,
  "rule_adjustment": 0.06,
  "components": {
    "competition": 0.65,
    "transport": 0.91,
    "audience": 0.93
  }
}
```

## Result

All scoring decisions pass through one testable component.

---

# 11. Phase 8 — Point Analysis API

## Goal

Expose the complete pipeline through FastAPI.

## Endpoint

```text
POST /api/v1/analysis/point
```

Pipeline:

```text
Request
  ↓
Validation
  ↓
Geo Data
  ↓
Feature Engineering
  ↓
Scoring
  ↓
Rules
  ↓
Decision Engine
  ↓
Explanation
  ↓
Response
```

Add integration tests.

## Result

One API call performs a complete location analysis.

---

# 12. Phase 9 — Frontend Map

## Goal

Make the system usable visually.

## Stack

```text
React
TypeScript
MapLibre GL JS
```

## Tasks

Implement:

```text
interactive map
location search
point selection
business-type selector
analysis button
result panel
```

Display analysis radius.

Display relevant POIs.

Result panel:

```text
Suitability: 87/100

Transport       91
Target audience 93
Competition     65
Commercial      82
```

## Result

The user can interactively analyze a location.

---

# 13. Phase 10 — Area Analysis

## Goal

Move from point scoring to actual location discovery.

## Tasks

Allow selection of:

```text
bounding box
district
polygon
```

Generate candidate grid.

Example:

```text
grid spacing = 300 m
```

Pipeline:

```text
Selected area
     ↓
Candidate generator
     ↓
Geo data
     ↓
Features
     ↓
Scores
     ↓
Ranking
```

Endpoint:

```text
POST /api/v1/analysis/area
```

## Important

Do NOT make separate Overpass queries for every candidate.

Fetch geographic data for the complete analysis region where possible and calculate local candidate features from the shared dataset.

## Result

The system evaluates dozens/hundreds of candidate locations efficiently.

---

# 14. Phase 11 — Heatmap

## Goal

Visualize location suitability spatially.

## Tasks

Return:

```json
[
  {
    "lat": 60.17,
    "lon": 24.94,
    "score": 0.91
  }
]
```

Render heatmap.

Conceptual mapping:

```text
low suitability    → red
medium suitability → yellow/orange
high suitability   → green
```

Also show top candidate markers.

## Result

The user can visually identify promising areas.

---

# 15. Phase 12 — Ranking

## Goal

Turn area analysis into a recommendation system.

Sort candidate locations by score.

Return:

```text
Top locations

1. Candidate A — 0.91
2. Candidate B — 0.87
3. Candidate C — 0.84
...
```

Support:

```text
Top 5
Top 10
Top 20
```

Later allow ranking by additional constraints.

---

# 16. Phase 13 — Data Collection for ML

## Goal

Create a real dataset instead of inventing training labels.

This phase requires careful design.

Possible supervision signals may include:

```text
existing successful business locations
business density
survival/open-close history if obtainable
ratings/review volume where legally and technically available
commercial activity proxies
foot-traffic/open-data datasets
```

Create dataset:

```text
location
business_type
features
target
timestamp
city
```

Store dataset provenance.

## Critical Rule

Do not create fake labels such as:

```text
good_location = 1
```

based purely on intuition and then present the resulting model as trained intelligence.

If true outcome labels are unavailable, keep the deterministic model and explicitly frame ML experiments as proxy-based.

---

# 17. Phase 14 — ML Baseline

## Goal

Train first reproducible models.

Start with:

```text
Logistic Regression
Random Forest
Gradient Boosting
```

Potentially:

```text
XGBoost
LightGBM
```

Create reproducible training pipeline:

```text
dataset
   ↓
preprocessing
   ↓
split
   ↓
training
   ↓
evaluation
   ↓
artifact
```

Store model metadata:

```text
model version
feature version
training timestamp
dataset version
metrics
```

---

# 18. Phase 15 — Spatial Validation

## Goal

Avoid misleading ML results caused by geographic leakage.

Do not rely only on random:

```python
train_test_split(...)
```

Test geographic splits.

Example:

```text
Train:
Kamppi
Kallio
Töölö

Test:
Pasila
```

Later:

```text
Train:
Helsinki

Test:
Espoo
```

Compare:

```text
heuristic baseline
vs
ML model
```

Document results.

---

# 19. Phase 16 — Ranking ML

## Goal

Move from independent classification/regression toward actual recommendation ranking.

Research:

```text
Learning to Rank
LightGBM Ranker
XGBoost ranking
pairwise ranking
```

Input:

```text
business requirements
+
candidate location features
```

Output:

```text
ordered candidate locations
```

Evaluate using:

```text
NDCG@K
MAP
Precision@K
```

This should become the long-term ML direction of the project.

---

# 20. Phase 17 — Explainable ML

## Goal

Explain why ML ranked a location highly.

For tree models investigate:

```text
SHAP
```

Expose top positive and negative features.

Example:

```text
+ office_density        +0.14
+ transport_access      +0.11
+ university_proximity  +0.08
- competitor_density    -0.09
```

Combine this with Rule Engine explanations.

---

# 21. Phase 18 — Business-Type Profiles

## Goal

Generalize beyond coffee shops.

Add:

```text
restaurant
gym
pharmacy
supermarket
coworking
beauty salon
```

Each business type should define:

```text
relevant POIs
feature weights
rules
model configuration
```

Example configuration:

```yaml
coffee_shop:
  positive_features:
    - universities
    - offices
    - transit

  competitors:
    - cafe
    - coffee_shop
```

Do not implement separate pipelines for each business type.

---

# 22. Phase 19 — Persistence

Persist analyses.

Entities:

```text
Analysis
Candidate
FeatureSnapshot
Prediction
RuleResult
```

Allow:

```text
analysis history
result comparison
reproducibility
```

A stored analysis should retain enough information to understand how its result was produced.

---

# 23. Phase 20 — Background Jobs

Area analysis may become expensive.

When required, introduce:

```text
Redis
+
Celery / RQ / Arq
```

Flow:

```text
POST analysis
      ↓
202 Accepted
      ↓
background processing
      ↓
GET analysis/{id}
```

Possible statuses:

```text
pending
processing
completed
failed
```

---

# 24. Phase 21 — Performance Optimization

Measure before optimizing.

Track:

```text
Overpass latency
feature extraction latency
candidate scoring latency
DB query latency
ML inference latency
total analysis latency
```

Optimize:

```text
batch queries
PostGIS indexes
Redis caching
shared area datasets
vectorized feature computation
```

Target point-analysis latency:

```text
< 2 seconds when geographic data is cached
```

Large area analysis may execute asynchronously.

---

# 25. Phase 22 — Production Hardening

Add:

```text
structured logging
request IDs
analysis IDs
error handlers
timeouts
retries
rate limiting
health checks
readiness checks
```

Add CI pipeline:

```text
lint
type check
tests
build
```

Provide Docker production configuration.

---

# 26. Phase 23 — Portfolio Documentation

README should clearly demonstrate engineering depth.

Include:

```text
problem
demo screenshots
architecture
system diagram
data pipeline
ML pipeline
feature engineering
rule engine
PostGIS usage
model evaluation
API examples
Docker startup
technical decisions
limitations
future improvements
```

Create architecture diagram:

```text
User
 ↓
React + MapLibre
 ↓
FastAPI
 ↓
Analysis Service
 ├── Geo Service → OSM / Overpass
 ├── Feature Engine → PostGIS
 ├── Rule Engine
 ├── ML Model
 └── Decision Engine
 ↓
PostgreSQL / PostGIS
```

---

# 27. Recommended Development Order

Execute the project in this order:

```text
01 Repository setup
        ↓
02 FastAPI
        ↓
03 PostgreSQL/PostGIS
        ↓
04 Geographic domain
        ↓
05 Nominatim
        ↓
06 Overpass
        ↓
07 POI normalization
        ↓
08 Feature engineering
        ↓
09 Baseline scoring
        ↓
10 Rule Engine
        ↓
11 Decision Engine
        ↓
12 Point Analysis API
        ↓
13 Map frontend
        ↓
14 Area candidate generation
        ↓
15 Efficient area feature extraction
        ↓
16 Heatmap
        ↓
17 Ranking
        ↓
18 Dataset pipeline
        ↓
19 ML experiments
        ↓
20 Spatial validation
        ↓
21 ML inference integration
        ↓
22 SHAP
        ↓
23 Multiple business types
        ↓
24 Background jobs
        ↓
25 Production hardening
        ↓
26 Deployment
```

Do not start by training an ML model.

First build a reliable geospatial data pipeline and deterministic baseline.

---

# 28. MVP Milestone

MVP is reached when this complete scenario works:

```text
User opens Helsinki
        ↓
selects "Coffee Shop"
        ↓
clicks a location
        ↓
backend obtains geographic data
        ↓
features are calculated
        ↓
baseline + rules evaluate location
        ↓
score = 87/100
        ↓
user sees explanation
```

Example:

```text
87/100 — High suitability

Positive:
+ 14 public transport stops within 500 m
+ high office concentration
+ university within 800 m
+ high surrounding commercial activity

Negative:
- 11 competing cafés within 500 m
- limited parking availability
```

At this milestone, ML training is not required.

---

# 29. Portfolio Milestone

The project becomes portfolio-ready when it additionally supports:

```text
area analysis
+
heatmap
+
location ranking
+
PostGIS
+
Redis caching
+
trained ML model
+
baseline comparison
+
spatial validation
+
explainability
+
Docker
+
tests
+
CI
+
public demo
```

The final portfolio story should demonstrate an end-to-end system:

```text
Geospatial Data
       ↓
Data Engineering
       ↓
Feature Engineering
       ↓
ML / Ranking
       ↓
Rule Engine
       ↓
Decision Engine
       ↓
Explainability
       ↓
FastAPI
       ↓
Interactive Map
```

---

# 30. Advanced Roadmap

After the core project is stable, consider:

```text
Google Places integration
city open-data integration
demographic datasets
real estate/rent prices
pedestrian traffic datasets
public transport accessibility
competitor clustering
H3 spatial indexing
multi-city support
time-aware features
business survival prediction
scenario simulation
```

H3 is particularly interesting for replacing an arbitrary rectangular grid with standardized geographic cells.

Potential later architecture:

```text
City
 ↓
H3 cells
 ↓
Feature Store
 ↓
Business-specific ranking
 ↓
Top-K cells
 ↓
Detailed candidate analysis
```

---

# 31. LLM Layer — Optional

An LLM is NOT required for the core scoring system.

Do not introduce an LLM merely to label the project as AI.

A later LLM layer may convert structured analysis into natural-language explanations.

Input:

```json
{
  "score": 0.87,
  "positive_factors": [...],
  "negative_factors": [...],
  "business_type": "coffee_shop"
}
```

Output:

```text
This location has strong potential for a coffee shop because...
```

The LLM must only explain supplied evidence.

It must not generate geographic facts or modify calculated scores.

---

# 32. Final Target

The mature version of GeoMarket AI should implement:

```text
Business requirements
        +
Geospatial data
        +
Demographic / commercial data
        ↓
Feature Engineering
        ↓
┌──────────────────────────┐
│ ML / Learning-to-Rank    │
└────────────┬─────────────┘
             +
┌────────────▼─────────────┐
│ Expert Rule Engine       │
└────────────┬─────────────┘
             ↓
      Decision Engine
             ↓
       Explainability
             ↓
    Ranked Locations
             ↓
     Interactive Map
```

The system's central engineering principle is:

> Collect evidence first, derive features second, score third, explain last.

The model must never substitute for missing geographic evidence.
