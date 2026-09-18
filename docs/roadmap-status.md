# Roadmap status

The repository completes the end-to-end MVP milestone in `PLAN.md`. The later roadmap contains
research and deployment work whose prerequisites are external to the source tree.

| Plan phases | Status | Evidence / gate |
| --- | --- | --- |
| 0–3 foundation and external geo | Complete | Docker topology, typed domain, Nominatim, Overpass, Redis cache |
| 4–8 point pipeline | Complete | Features, deterministic model, rules, decisions, explanations, typed API |
| 9–12 visual discovery | Complete | Map selection/search, bounded area analysis, heatmap, top-N ranking |
| 13–17 trained/ranking ML | Gated | Requires legal, provenance-documented outcome labels and spatial evaluation |
| 18 business profiles | Extensible | Central coffee-shop profile exists; more profiles require domain validation |
| 19 persistence | Foundation | PostGIS entities, index, query boundary, and migration exist; history API is pending |
| 20 background jobs | Deferred by design | Introduce only after measured synchronous area latency requires it |
| 21–23 hardening/docs | MVP complete | Structured logs, constraints, caching, CI, Docker, architecture and API docs |
| Deployment/public demo | External | Requires target infrastructure, secrets, domain, and production tile policy |

No model quality, dataset provenance, or public deployment is claimed where no evidence exists.

