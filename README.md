# GeoMarket AI

GeoMarket AI is an explainable geospatial decision-support MVP for answering: **how suitable is
this location for a coffee shop?** It combines live OpenStreetMap evidence, deterministic feature
engineering, a transparent scoring baseline, explicit expert rules, and an interactive Helsinki
map. It also ranks candidates across a visible area without making one external request per point.

## What works

- Search through Nominatim and cached POI retrieval with sequential Overpass failover
- Redis caching for external responses
- Point scoring with 15 geographic features, six score components, confidence, and traceable rules
- Click-to-select base points with visible evidence markers, popups, and score results on the map
- Bounded area-grid generation, a shared region fetch, ranking, and heatmap display
- Typed FastAPI and React/TypeScript contracts
- PostgreSQL/PostGIS schema and radius-query boundary with an initial Alembic migration
- Docker Compose for frontend, backend, PostGIS, and Redis
- Unit/API tests, Ruff, strict mypy, TypeScript checks, dependency audit, and CI

## Run locally

Requirements: Python 3.12+, Node 22+, and Docker. Python dependencies and commands stay inside the
project virtual environment.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
Copy-Item .env.example .env
docker compose up --build
```

Open <http://localhost:5173>. API docs are at <http://localhost:8000/docs>.
If those ports are occupied, set `BACKEND_PORT`, `FRONTEND_PORT`, and the browser-facing
`VITE_API_URL` in `.env`, then rebuild the frontend image.

For backend-only development, run infrastructure with Docker and the API from the venv:

```powershell
docker compose up -d postgres redis
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Run every local quality gate:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

## API

```text
GET  /health
GET  /api/v1/business-types
GET  /api/v1/geo/search?q=Kamppi
POST /api/v1/analysis/point
POST /api/v1/analysis/area
```

Example point request:

```json
{
  "business_type": "coffee_shop",
  "latitude": 60.1699,
  "longitude": 24.9384,
  "radius_m": 1000,
  "target_audience": ["students", "office_workers"]
}
```

See [architecture](docs/architecture.md) for component boundaries and score semantics.
The [roadmap status](docs/roadmap-status.md) maps implementation evidence and external gates to the
phases in `PLAN.md`.
For a hands-on code-reading and refactoring curriculum, follow the
[MVP-to-portfolio roadmap](docs/portfolio-roadmap.md) one stage and one pull request at a time.

## Honest limitations and next gates

The current score is a deterministic decision-support baseline, not a claim of business success.
The repository intentionally contains no fabricated labels, metrics, or model artifact. PLAN phases
13–17 require an independently sourced outcome/proxy dataset with provenance, geographic holdout
evaluation, baseline comparison, and versioned artifacts before a trained model can be shipped.
Persistence models and migrations exist, but request history endpoints and background jobs remain
future hardening once synchronous area-analysis latency demonstrates the need. A public deployment
also requires infrastructure credentials and an appropriate map-tile provider.

OpenStreetMap data may be incomplete. The score and confidence should support—not replace—local
market research, rent analysis, permits, and professional judgment.
