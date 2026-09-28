# PLAN.md — GeoMarket AI Development Plan

> **Current working plan:** use [Section 27A](#27a-collaborative-execution-plan--mlds-learning-track)
> for step-by-step ownership. Your tasks are limited to ML, data science, and research; the AI agent
> owns the surrounding engineering work.

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

# 27A. Collaborative Execution Plan — ML/DS Learning Track

This section turns the product roadmap into the working plan from the repository's current state.
It incorporates the delivery and learning practices in
[`docs/portfolio-roadmap.md`](docs/portfolio-roadmap.md). Follow the phases in order and use one
branch and one pull request per numbered phase. Do not begin a phase until its entry gate is met.

## Ownership contract

Every task has exactly one primary owner:

```text
[YOU — ML/DS/RESEARCH]
    Work that develops data science judgment: problem formulation, source research,
    data auditing, feature hypotheses, statistical analysis, experiments, validation,
    model interpretation, and evidence-based conclusions.

[AI AGENT — ENGINEERING]
    All other work: backend, frontend, APIs, database, PostGIS, ETL production code,
    integrations, migrations, infrastructure, security, observability, deployment,
    automated tests, and documentation wiring.
```

The AI agent may explain concepts, review your notebook/code, suggest experiments, and help debug
tooling. It must not silently make the research decision, invent labels, choose the winning model,
run the final evaluation on your behalf, or write conclusions unsupported by your results. The AI
agent should productionize your accepted ML/DS artifacts only after you can explain and defend them.

For each phase:

1. The AI agent creates or updates the phase issue with scope, interfaces, and acceptance checks.
2. Read the relevant request/data path before changing it and record inputs, outputs, side effects,
   and failure modes.
3. The AI agent completes engineering prerequisites and characterization tests.
4. You complete only the listed ML/DS/research tasks and record decisions with evidence.
5. The AI agent reviews reproducibility and integrates the accepted output into production code.
6. Run `powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1`.
7. Close the phase with a short report: problem, method, result, limitations, and next gate.

Use `test:`, `refactor:`, `feat:`, `fix:`, `perf:`, `docs:`, `data:`, and `ml:` commit prefixes.
Raw data, processed data, feature schemas, and model artifacts must have explicit versions and must
not be committed when their license, size, or sensitivity makes that inappropriate.

## Current checkpoint

The repository has a working Phase 0–12 product path: point analysis, area candidates, heuristic
scoring, rules, explanations, ranking, and map visualization. It is not yet a trained intelligent
system. Before `PLAN.md` Phase 13 begins, the incomplete MVP boundaries below must be made
trustworthy and reproducible.

```text
Current capability: deterministic geospatial MVP
Current execution phase: Collaborative Phase 1 below
Next ML gate: Collaborative Phase 4 — dataset design and source research
```

## Collaborative Phase 1 — Freeze and measure the current baseline

**Purpose:** establish evidence that later changes and models can be compared against.

### AI agent responsibilities

- [ ] Record the current commit, environment, configuration, test count, coverage, image sizes, and
      frontend bundle size.
- [ ] Add a reproducible benchmark command for point cache miss/hit and 25/100/400-candidate areas.
- [ ] Capture one license-compliant Helsinki response fixture with retrieval date and attribution.
- [ ] Verify migrations, PostGIS tables, the GiST index, Redis behavior, and Docker smoke tests.
- [ ] Add five small tracked issues for the next engineering phase.
- [ ] Document how to reproduce all baseline measurements from a fresh clone.

### Your ML/DS/research responsibilities

- [ ] Read the current feature, baseline-model, rule, and decision code as one scoring pipeline.
- [ ] Create `docs/research/baseline-assumptions.md` listing every feature, threshold, weight, rule,
      expected direction, and possible double-counting relationship.
- [ ] Formulate at least five falsifiable critiques of the current score, for example whether café
      density represents competition, demand, or both.
- [ ] Define what the current score can and cannot claim. Do not describe it as predicted business
      success, probability, or model confidence.

### Exit gate

- [ ] The existing result can be reproduced, timed, and explained feature by feature.
- [ ] Baseline limitations are written before any weights or models are changed.

## Collaborative Phase 2 — Complete the trustworthy deterministic product

**Purpose:** remove misleading contracts and make every score reproducible before collecting labels.

### AI agent responsibilities

- [ ] Refactor backend boundaries using small `Geocoder`, `POIProvider`, `Cache`, and repository
      protocols; reuse and close long-lived HTTP/Redis resources correctly.
- [ ] Split API routers and centralize typed integration errors and FastAPI error handling.
- [ ] Make `target_audience` a typed input and pass it to constraint/decision logic instead of
      silently ignoring it.
- [ ] Rename heuristic `confidence` to `evidence_coverage`, or document and expose both concepts
      separately without an API-breaking silent change.
- [ ] Move all weights, thresholds, saturation points, radii, and rules into validated, versioned
      business profiles.
- [ ] Return the complete candidate surface for heatmaps and a separate top-N ranking.
- [ ] Display the selected radius and evidence completeness in the frontend.
- [ ] Add characterization, monotonicity, bounds, conflicting-rule, API, and frontend interaction
      tests.

### Your ML/DS/research responsibilities

- [ ] Define the supported audience segments and state the evidence proxy for each segment.
- [ ] Create the first feature dictionary with definition, source, unit, radius, valid range,
      missing-value meaning, expected direction, and known bias.
- [ ] Propose hypotheses for ambiguous effects, especially competition versus demand and centrality
      versus neighborhood opportunity.
- [ ] Design a sensitivity-analysis matrix showing which raw feature should change which component
      and under what assumptions.
- [ ] Review sensitivity results and recommend profile changes; label these as expert calibration,
      not model training.

### Exit gate

- [ ] Every displayed score identifies feature-schema, profile, rule, and scoring versions.
- [ ] Every accepted input affects behavior or is removed from the public contract.
- [ ] A reviewer can trace each score contribution back to evidence and an explicit assumption.

## Collaborative Phase 3 — Persistence, spatial validity, and reproducibility

**Purpose:** ensure candidates are real geographic opportunities and analyses can be audited later.

### AI agent responsibilities

- [ ] Implement async SQLAlchemy sessions and repositories for analyses, candidates, feature
      snapshots, predictions, rule results, and provider metadata.
- [ ] Add analysis history and paginated candidate endpoints.
- [ ] Add polygon/district models, validity checks, and PostGIS radius, containment, intersection,
      and nearest-neighbor queries.
- [ ] Add a city registry so Helsinki center and bounds are not hard-coded.
- [ ] Filter or flag candidates on water, restricted land, major roads, and clearly non-commercial
      surfaces using versioned rules and source data.
- [ ] Compare Python grid, PostGIS grid, and H3 only with a reproducible benchmark before choosing.
- [ ] Add migration, transaction, spatial-boundary, rollback, and query-plan integration tests.

### Your ML/DS/research responsibilities

- [ ] Research what constitutes an eligible coffee-shop candidate and distinguish hard exclusions
      from soft suitability features.
- [ ] Review a stratified sample of accepted/rejected candidates and calculate disagreement/error
      categories for the validity rules.
- [ ] Define the spatial unit of observation to carry into dataset work: point, parcel, building,
      regular grid cell, or H3 cell, with documented trade-offs.
- [ ] Write a short research decision explaining whether accessibility should use radial distance,
      walking-network distance, travel time, or a staged combination.

### Exit gate

- [ ] A stored analysis can reproduce the same deterministic result from retained evidence.
- [ ] Candidate eligibility has a documented spatial unit and measured review results.

## Collaborative Phase 4 — Define the ML problem and research data sources

**Purpose:** begin original `PLAN.md` Phase 13 without inventing a target.

### AI agent responsibilities

- [ ] Provide a data-source registry format containing URL/provider, license, access method,
      geography, temporal coverage, update cadence, and ingestion status.
- [ ] Scaffold immutable raw-data storage, checksums, metadata manifests, and dataset versioning.
- [ ] Add safe connector interfaces and small source probes only after license/access approval.
- [ ] Create a data-card template and an automated validation command, but leave research fields and
      conclusions for you.

### Your ML/DS/research responsibilities

- [ ] Write the decision question in one sentence and define the unit of observation.
- [ ] Compare candidate targets such as 12/24-month survival, closure risk, sales, rent-adjusted
      revenue, or review-volume growth. Reject targets that merely reproduce heuristic rules.
- [ ] Research legally usable sources for outcomes, historical businesses, demographics,
      employment, transit frequency, pedestrian activity, rent, land use, and street networks.
- [ ] Record license, provenance, geographic/temporal coverage, access limitations, expected bias,
      and leakage risk for every source.
- [ ] Select one primary target and at most one explicitly named proxy target.
- [ ] Define observation time, prediction horizon, inclusion/exclusion criteria, and how openings,
      closures, relocations, chains, and missing outcomes are treated.
- [ ] Draft the dataset card: intended use, exclusions, ethical risks, known bias, refresh plan, and
      claims the dataset cannot support.

### Data gate

- [ ] The target is observable, legally usable, temporally aligned, and not derived from the current
      score.
- [ ] At least one source supports features as they existed at observation time.
- [ ] If this gate fails, stop ML work and continue improving the deterministic system. Do not create
      synthetic success labels and present them as truth.

## Collaborative Phase 5 — Build and audit dataset v1

**Purpose:** produce a reproducible, leakage-aware dataset suitable for honest experimentation.

### AI agent responsibilities

- [ ] Implement idempotent ingestion and transformation jobs from approved source specifications.
- [ ] Preserve immutable raw snapshots, checksums, retrieval metadata, schemas, and lineage.
- [ ] Implement deterministic spatial joins and point-in-time feature computation.
- [ ] Add schema checks for coordinates, timestamps, duplicates, ranges, and referential integrity.
- [ ] Provide one command that rebuilds the processed dataset from available raw snapshots.
- [ ] Keep exploratory code in notebooks and move reusable transforms into tested Python modules.

### Your ML/DS/research responsibilities

- [ ] Create an EDA notebook covering sample size, target distribution, missingness, outliers,
      coordinate errors, duplicates, temporal coverage, spatial clustering, and source overlap.
- [ ] Map the target and important features; inspect whether neighboring observations are near
      duplicates.
- [ ] Audit leakage feature by feature, including future information, post-opening reviews,
      contemporaneous competitors, and spatially duplicated records.
- [ ] Quantify class imbalance or target skew and propose evaluation implications without altering
      the final holdout.
- [ ] Define district/city/time grouping variables before model comparison.
- [ ] Freeze a final geographic or temporal holdout and record its checksum. Do not inspect its
      model results during feature/model selection.
- [ ] Finish dataset-card sections for quality, bias, exclusions, and fitness for use.

### Exit gate

- [ ] `dataset_v1` is reproducible, versioned, provenance-documented, and passes automated checks.
- [ ] The frozen holdout and leakage policy were defined before model selection.

## Collaborative Phase 6 — Feature research and deterministic baseline evaluation

**Purpose:** establish whether the existing feature space contains useful, stable signal.

### AI agent responsibilities

- [ ] Implement the accepted feature schema in a versioned offline/online-compatible feature module.
- [ ] Add point-in-time joins, missingness indicators, schema compatibility checks, and unit tests.
- [ ] Create reproducible experiment configuration and result-table formats.
- [ ] Ensure serving and training use the same feature definitions where applicable.

### Your ML/DS/research responsibilities

- [ ] Perform univariate and multivariate feature analysis using training data only.
- [ ] Investigate transformations for counts, densities, distance decay, ratios, network access, and
      spatial context.
- [ ] Evaluate missingness as information instead of silently replacing it with arbitrary values.
- [ ] Measure feature stability across districts and time periods.
- [ ] Detect redundant, highly correlated, target-leaking, or proxy-sensitive features.
- [ ] Evaluate the deterministic heuristic on the training/validation design using target-appropriate
      metrics. This is the required baseline for every later model.
- [ ] Publish a feature-selection rationale and baseline evaluation report, including negative
      findings.

### Exit gate

- [ ] Feature schema v1 and baseline metrics are frozen before trained-model comparison.
- [ ] Every retained feature has a source, timestamp rule, transformation, and justification.

## Collaborative Phase 7 — Train honest ML baselines

**Purpose:** learn whether a trained model improves the real target.

### AI agent responsibilities

- [ ] Add isolated training dependencies and reproducible CLI/configuration scaffolding.
- [ ] Add artifact storage conventions for data version, feature version, code commit, environment,
      seed, metrics, and model card.
- [ ] Add automated checks for determinism, schema mismatch, artifact loading, and inference shape.
- [ ] Keep training-only libraries out of the serving image unless production inference requires
      them.

### Your ML/DS/research responsibilities

- [ ] Choose metrics from the target before training: regression, classification, calibration, or
      ranking metrics as appropriate.
- [ ] Train a dummy baseline, a simple linear/logistic model, and at least one tree-based model using
      fixed seeds and pipelines.
- [ ] Use only the predefined geographic/temporal training and validation groups.
- [ ] Tune within training/validation data; do not repeatedly inspect the final holdout.
- [ ] Compare every model against the deterministic heuristic on identical observations and metrics.
- [ ] Analyze calibration, uncertainty, subgroup/geographic errors, residual maps, and concrete
      failure cases.
- [ ] Record experiments, including models that failed or did not beat the heuristic.
- [ ] Select a candidate only if improvement is meaningful, stable, and relevant to the decision
      problem; otherwise retain the deterministic baseline.
- [ ] Write the model card and model-selection report in your own words.

### Model gate

- [ ] The experiment is reproducible from a clean environment.
- [ ] The final holdout was untouched during selection.
- [ ] Deployment requires measurable improvement over the deterministic baseline, acceptable
      calibration/error behavior, and no unresolved leakage.

## Collaborative Phase 8 — Spatial validation and learning to rank

**Purpose:** move from plausible point predictions to trustworthy area recommendations.

### AI agent responsibilities

- [ ] Implement reusable geographic/temporal splitters from your approved design.
- [ ] Add ranking dataset/group construction and reproducible ranking experiment commands.
- [ ] Add evaluation-report generation without choosing conclusions or hiding failed runs.
- [ ] Add safeguards preventing train/test spatial overlap and accidental holdout reuse.

### Your ML/DS/research responsibilities

- [ ] Compare leave-one-district-out, leave-one-city-out, and temporal holdouts where data permits.
- [ ] Quantify how performance changes with distance from training regions and data-density bands.
- [ ] Define a ranking query/group, relevance target, and candidate set that match the product flow.
- [ ] Train and compare pointwise and pairwise/listwise approaches only if the target supports them.
- [ ] Evaluate NDCG@5/10, MAP, Precision@K, stability of the top-K, and geographic failure patterns.
- [ ] Compare ranking models with sorting the deterministic and supervised point scores.
- [ ] Decide whether ranking ML is justified and document limitations for unseen cities.

### Exit gate

- [ ] The chosen evaluation matches how users request and compare candidate locations.
- [ ] Generalization claims are limited to geographies and time periods supported by evidence.

## Collaborative Phase 9 — Production inference and explainability

**Purpose:** serve a validated model without losing traceability or the deterministic fallback.

### AI agent responsibilities

- [ ] Implement the accepted artifact behind `LocationScoringModel` without placing inference in API
      routes.
- [ ] Validate feature schema and model/profile versions at startup and per prediction.
- [ ] Retain the deterministic fallback and make fallback use visible in response metadata.
- [ ] Persist prediction inputs, artifact version, outputs, rule effects, and explanation evidence.
- [ ] Expose model contributions and uncertainty through typed APIs and accessible UI components.
- [ ] Add shadow-mode, rollback, corrupted-artifact, schema-mismatch, and fallback tests.

### Your ML/DS/research responsibilities

- [ ] Choose an explanation method appropriate to the accepted model.
- [ ] Validate global and local explanations for stability, direction, correlated-feature behavior,
      and reconciliation with predictions.
- [ ] Compare model explanations with rule effects and identify double counting or contradictions.
- [ ] Define out-of-distribution and low-evidence warning criteria using validation results.
- [ ] Write user-facing interpretation guidance that distinguishes association, prediction, and
      causation.

### Exit gate

- [ ] Every prediction is traceable to evidence, feature schema, model artifact, rules, and version.
- [ ] Explanations are tested model evidence, not LLM-generated geographic claims.

## Collaborative Phase 10 — Multi-business research and profiles

**Purpose:** prove the architecture generalizes without copying the coffee-shop pipeline.

### AI agent responsibilities

- [ ] Implement generic profile loading, validation, versioning, APIs, and frontend selection.
- [ ] Reuse candidate generation, features, decisions, persistence, and explanations across profiles.
- [ ] Add contract and regression tests proving that profiles do not create separate pipelines.

### Your ML/DS/research responsibilities

- [ ] Select the next business type based on obtainable outcomes and meaningful feature differences.
- [ ] Research its customer segments, competitors, complementary POIs, spatial scale, constraints,
      and measurable success target.
- [ ] Propose and validate its feature/profile specification using the same evidence standards.
- [ ] Determine whether an existing model transfers, needs recalibration, or requires a separate
      training dataset; support the conclusion with experiments.

### Exit gate

- [ ] A second business type works through shared infrastructure and has its own documented evidence.

## Collaborative Phase 11 — Security, observability, performance, and background work

**Purpose:** make the system diagnosable and safe without assigning non-ML engineering to you.

### AI agent responsibilities

- [ ] Add request/analysis IDs, structured event fields, readiness checks, and metrics for providers,
      cache, features, model inference, persistence, and total latency.
- [ ] Add bounded requests, polygon/candidate/radius limits, concurrency controls, rate limiting,
      secure headers, strict environment-specific CORS, and container hardening.
- [ ] Add reproducible performance benchmarks and profile before optimizing.
- [ ] Introduce a background job state machine and worker only if measured synchronous latency or
      reliability justifies it.
- [ ] Add CI integration tests with PostGIS/Redis plus dependency, secret, image, and migration scans.

### Your ML/DS/research responsibilities

- [ ] Define acceptable inference-latency and batch-scoring budgets based on experiment size and
      product usage assumptions.
- [ ] Test whether performance optimizations, approximations, or feature freshness changes alter
      model metrics or top-K stability.
- [ ] Define monitoring thresholds for feature drift, prediction drift, evidence coverage, and model
      degradation, including the statistical limitations of each alert.

### Exit gate

- [ ] A failed or slow analysis is explainable from telemetry.
- [ ] Performance changes preserve model quality within documented tolerances.

## Collaborative Phase 12 — Deployment and portfolio evidence

**Purpose:** publish a defensible project whose claims are backed by reproducible evidence.

### AI agent responsibilities

- [ ] Create development/production configurations, managed-secret integration, TLS, health checks,
      backups, restore tests, migration release steps, rollback, quotas, and monitoring.
- [ ] Publish versioned images with vulnerability scans, SBOMs, and immutable tags.
- [ ] Add a provider-independent seeded demo mode, staging smoke tests, screenshots, architecture
      diagrams, ADRs, runbook, API examples, and a short demo-video script.
- [ ] Put quick start, test status, architecture, limitations, and live/demo links above the README
      fold.

### Your ML/DS/research responsibilities

- [ ] Publish the final data card, feature dictionary, baseline report, spatial-validation report,
      model card, explainability examples, and limitations.
- [ ] Create the ML/DS portion of the case study: question, data provenance, leakage controls,
      experiment design, metrics, failures, final decision, and lessons learned.
- [ ] Verify every numerical ML claim against a reproducible result artifact.
- [ ] Prepare to explain why the split strategy, metrics, baseline, model, and uncertainty treatment
      match the business-location decision problem.

### Final gate

- [ ] A fresh clone passes setup, checks, migrations, and smoke tests.
- [ ] The public demo has a video/seeded fallback and documented operating limits.
- [ ] ML claims exist only if the data and model gates passed; otherwise the project explicitly ships
      the validated deterministic system and documents why that was the honest decision.

## Your ML/DS learning outcomes

By completing only your assigned tasks, you should be able to demonstrate and explain:

```text
problem and target formulation
data-source and license research
data cards, lineage, and dataset versioning
geospatial exploratory data analysis
missingness, bias, and leakage audits
feature hypotheses and sensitivity analysis
spatial and temporal cross-validation
baseline design and fair model comparison
classification/regression/ranking metrics
calibration, uncertainty, and subgroup errors
learning-to-rank and top-K evaluation
SHAP or appropriate model explanations
drift monitoring and model limitations
reproducible experiment and model cards
```

The objective is not merely to deploy a model. The objective is for you to be able to defend every
data and modeling decision while the AI agent handles the surrounding production engineering.

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
