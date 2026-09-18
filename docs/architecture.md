# Architecture

GeoMarket AI is a modular monolith. HTTP adapters depend on application services; the scoring,
rules, feature engineering, and domain models do not depend on FastAPI or persistence.

```text
React + MapLibre
       |
       v
FastAPI routes -- Nominatim search
       |
AnalysisService -- Overpass + Redis cache
       |
       +-- FeatureEngine
       +-- LocationScoringModel (deterministic baseline today)
       +-- RuleEngine
       +-- DecisionEngine / explanations
       |
PostgreSQL + PostGIS persistence boundary
```

Area analysis generates a bounded grid, fetches the complete region from Overpass once, and reuses
that normalized POI set for every candidate. This avoids the prohibited candidates × features
network request pattern. Geographic persistence uses SRID 4326 `Geography(POINT)` and GiST.

## Score contract

All internal and API scores use `0.0..1.0`. The UI alone converts these values to `0..100`. The
baseline is a configured weighted sum of normalized components. Rules are separately returned with
their modifier and evidence, and only `DecisionEngine` combines them.

## ML boundary

`LocationScoringModel` is the inference abstraction. A trained implementation can replace the
baseline without changing routes or decision logic. No trained artifact is included because the
repository has no defensible outcome labels yet. Model work is gated on a provenance-documented
dataset and geographic holdout evaluation against this baseline.

