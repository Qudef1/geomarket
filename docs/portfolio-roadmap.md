# From MVP to portfolio-ready GeoMarket AI

This is both a delivery roadmap and a code-reading/refactoring course. Follow it in order. Do not
start the ML stages until the data gate is satisfied, and do not refactor several boundaries in one
commit. The portfolio result should show evidence: tests, measurements, diagrams, migrations,
evaluation reports, and a deployed demo—not a long list of technologies.

## How to work through the roadmap

Use one branch and one pull request per numbered stage. Before changing a module:

1. Read it without editing and write its inputs, outputs, side effects, and failure modes.
2. Draw the call path and run the closest tests with `-vv`.
3. Add a characterization test for behavior you might accidentally change.
4. Refactor in small commits; keep behavior and API responses unchanged.
5. Run `powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1`.
6. Write a short PR description: problem, design, trade-off, evidence, and rollback.

Use commit prefixes consistently: `test:`, `refactor:`, `feat:`, `fix:`, `perf:`, `docs:`, and
`chore:`. A useful refactor commit changes structure but not observable behavior. If behavior changes,
split it into a separate `feat:` or `fix:` commit.

## First code-reading tour

Read one vertical request path rather than every file alphabetically:

```text
frontend/src/App.tsx
  -> frontend/src/api.ts
  -> backend/app/api/routes.py
  -> backend/app/services/analysis.py
  -> integrations/overpass.py
  -> services/features.py
  -> ml/models.py + services/rules.py
  -> services/decision.py
  -> API response -> MapView.tsx
```

Then read the cross-cutting boundaries: `core/config.py`, `api/dependencies.py`,
`integrations/cache.py`, `db/models.py`, migrations, Docker Compose, and CI. For each file, answer:

- Which layer owns it, and may that layer import this dependency?
- Is it pure calculation or I/O? What can fail?
- Which test proves its contract?
- What would have to change to replace Redis, Overpass, or the scoring model?
- Is a value evidence, configuration, a default, or an unexplained magic number?

## Stage 0 — Establish a trustworthy baseline

Goal: reproduce the project before refactoring it.

- [ ] Replace `contact@example.com` in local configuration with a real project contact.
- [ ] Build and start all containers; save `docker compose ps` and smoke-test output.
- [ ] Run the Alembic upgrade against PostGIS and inspect both tables and the GiST index.
- [ ] Save one permitted Helsinki point response as a test fixture with retrieval date and license.
- [ ] Record current test coverage, point latency on cache miss/hit, image sizes, and bundle size.
- [ ] Open five small GitHub issues for the next stage instead of keeping work only in notes.

Done when a fresh clone can follow the README without undocumented steps and all checks pass.

Read: [Docker build best practices](https://docs.docker.com/build/building/best-practices/),
[Compose production guidance](https://docs.docker.com/compose/how-tos/production/), and
[Vite production builds](https://vite.dev/guide/build).

## Stage 1 — Refactor the backend boundaries

Goal: practice changing design without changing results.

- [ ] Split `api/routes.py` into `analysis`, `geo`, and `business_types` routers.
- [ ] Introduce small `Geocoder`, `POIProvider`, `Cache`, and `AnalysisRepository` protocols.
- [ ] Make `AnalysisService` depend on protocols, not concrete clients.
- [ ] Replace module-level dependency construction with application-lifespan resources; close the
      Redis and HTTP clients cleanly at shutdown.
- [ ] Reuse long-lived `httpx.AsyncClient` instances rather than opening one per request.
- [ ] Define typed integration exceptions and one FastAPI exception-handler layer.
- [ ] Separate business-profile configuration from the coffee-shop implementation.
- [ ] Add architecture dependency tests or import rules so domain/scoring cannot import FastAPI,
      Redis, SQLAlchemy, or HTTPX.

Refactoring exercises: extract method, move function, replace concrete dependency with protocol,
replace conditionals with policy objects, and remove duplication. Avoid a generic repository or
event bus until two real consumers prove the abstraction.

Done when existing API snapshots are unchanged, unit tests no longer need concrete integrations,
and resource cleanup is tested.

Read: [FastAPI larger applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/),
[dependency injection](https://fastapi.tiangolo.com/tutorial/dependencies/),
[dependencies with `yield`](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/),
[SQLAlchemy asyncio](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html), and
[Redis asyncio lifecycle](https://redis.io/docs/latest/develop/clients/redis-py/async/).

## Stage 2 — Complete persistence and reproducibility

Goal: every recommendation can be retrieved and audited later.

- [ ] Add an async engine and one `AsyncSession` per request/task.
- [ ] Implement repositories for analyses, candidates, feature snapshots, predictions, and rules.
- [ ] Persist status, request parameters, provider timestamps, feature schema version, scoring-model
      version, rule version, and raw-data/cache references.
- [ ] Implement `GET /analysis/{id}` and `GET /analysis/{id}/candidates` with pagination.
- [ ] Make point analysis transactional; define what happens if persistence fails after scoring.
- [ ] Add migration upgrade/downgrade tests against real PostGIS in CI.
- [ ] Add integration tests for rollback, cascade deletion, JSON round trips, and spatial indexes.
- [ ] Review every autogenerated migration by hand.

Done when the same stored evidence can reproduce the same deterministic score and a migration can
upgrade an empty database and downgrade it cleanly.

Read: [SQLAlchemy ORM tutorial](https://docs.sqlalchemy.org/en/20/orm/),
[session lifecycle](https://docs.sqlalchemy.org/en/20/orm/session_basics.html),
[Alembic autogenerate and its limits](https://alembic.sqlalchemy.org/en/latest/autogenerate.html),
and [GitHub PostgreSQL service containers](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers).

## Stage 3 — Make geospatial work database-native

Goal: demonstrate genuine PostGIS engineering rather than storing points only.

- [ ] Add district/polygon domain models with SRID rules and validity checks.
- [ ] Move persisted radius, containment, intersection, and nearest-neighbor queries to PostGIS.
- [ ] Compare `geography` and projected `geometry` for Helsinki and document the decision.
- [ ] Use `ST_DWithin` for indexed radius filtering and `EXPLAIN (ANALYZE, BUFFERS)` to prove it.
- [ ] Add GiST indexes and regression tests for boundary points, invalid polygons, and antimeridian
      assumptions.
- [ ] Decide whether grid candidates remain generated in Python, move to PostGIS, or become H3;
      benchmark first.
- [ ] Add a city registry so Helsinki center and bounds are not hard-coded in analysis logic.

Done when spatial SQL is covered by integration tests and the documentation includes query plans and
measured behavior.

Read: [PostGIS `ST_DWithin`](https://postgis.net/docs/ST_DWithin.html) and
[the PostGIS radius-query recommendation](https://postgis.net/documentation/tips/st-dwithin/).

## Stage 4 — Harden external data ingestion

Goal: behave responsibly and predictably when public services are slow or incomplete.

- [ ] Respect the public Nominatim maximum, identification, attribution, and cache requirements;
      never turn search into client-side autocomplete.
- [ ] Add application-level Nominatim throttling and request coalescing.
- [ ] Reuse HTTP clients with connect/read/pool timeouts and bounded connection pools.
- [ ] Add bounded retries with jitter only for safe transient failures; never retry every 4xx.
- [ ] Implement Redis cache versioning, hit/miss metrics, negative caching, and stampede protection.
- [ ] Distinguish missing data, partial data, stale cache, and provider failure in result metadata.
- [ ] Store provider attribution/provenance and show OSM attribution visibly in the UI.
- [ ] Make provider URLs configurable so production can use hosted or self-managed services.
- [ ] Add contract fixtures for nodes, ways, relations, duplicates, centers, missing tags, malformed
      elements, 429, timeout, and invalid JSON responses.

Done when tests never call public services, one manual smoke test follows provider policies, and the
UI clearly tells users when evidence is incomplete.

Read before implementation: [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/),
[Overpass API documentation](https://wiki.openstreetmap.org/wiki/Overpass_API),
[OSM license and attribution FAQ](https://osmfoundation.org/wiki/Licence_and_Legal_FAQ),
[Redis cache-aside](https://redis.io/docs/latest/develop/use-cases/cache-aside/redis-py/), and
[Redis production checklist](https://redis.io/docs/latest/develop/clients/redis-py/produsage/).

## Stage 5 — Improve scoring as a product feature

Goal: make the deterministic baseline defensible and configurable before ML.

- [ ] Write a feature dictionary: definition, source tags, unit, radius, missing-value behavior,
      expected direction, valid range, and version.
- [ ] Move all thresholds, saturation points, weights, and rules into validated business profiles.
- [ ] Add profile-version and feature-schema-version fields to every result.
- [ ] Add restaurant and pharmacy profiles through the same pipeline—no copied service classes.
- [ ] Add sensitivity tests showing how each raw feature changes components and final score.
- [ ] Test monotonic expectations, score bounds, weight totals, and conflicting rules.
- [ ] Hold a small expert/user review and record why weights changed; do not call this model training.

Done when a reviewer can trace any displayed number back to versioned evidence and configuration.

## Stage 6 — Refactor and test the frontend

Goal: turn the single-screen prototype into a maintainable, accessible application.

- [ ] Split `App.tsx` into search, configuration, result, ranking, and map-layer components.
- [ ] Represent async behavior as explicit idle/loading/success/empty/error states; consider a reducer
      before introducing a state library.
- [ ] Generate frontend API types from the FastAPI OpenAPI document or validate responses at runtime.
- [ ] Add debounced search only if the selected provider permits that interaction; public Nominatim
      explicitly forbids autocomplete.
- [ ] Add abortable requests, stale-response protection, retry UI, loading skeletons, and empty states.
- [ ] Add keyboard map alternatives, visible focus, form labels, color-independent score cues, and
      responsive tests.
- [ ] Add component tests with user-level interactions and end-to-end tests for point/area flows.
- [ ] Lazy-load MapLibre or split the bundle; compare the bundle report before and after.
- [ ] Replace demo tiles with a production-appropriate provider and visible attribution.

Done when the two main workflows pass end-to-end tests at desktop and mobile sizes and an accessibility
audit has no serious findings.

Read: [React state guidance](https://react.dev/learn/managing-state),
[TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro),
[MapLibre examples](https://maplibre.org/maplibre-gl-js/docs/examples/), and
[MapLibre heatmaps](https://maplibre.org/maplibre-gl-js/docs/examples/create-a-heatmap-layer/).

## Stage 7 — Security and abuse resistance

Goal: prevent one request or configuration mistake from causing excessive work or exposure.

- [ ] Threat-model public endpoints, assets, external providers, cache keys, and stored analyses.
- [ ] Enforce polygon area/vertex, bounding-box, candidate-count, radius, request-size, timeout, and
      concurrency limits on the server.
- [ ] Add rate limiting with stable client identity and explicit `429` responses.
- [ ] Use strict CORS per environment and secure HTTP headers at the reverse proxy.
- [ ] Run containers as non-root, pin base-image versions/digests, add `.dockerignore`, scan images,
      and keep secrets out of images, logs, Compose, and Git.
- [ ] Add dependency updates and secret scanning to CI; document vulnerability response.
- [ ] Add authentication only if saved private analyses or multiple users become real requirements.

Done when abuse cases have automated tests and the threat model lists mitigations and accepted risks.

Read: [OWASP API Security Top 10](https://owasp.org/API-Security/),
[Docker build best practices](https://docs.docker.com/build/building/best-practices/), and
[Compose environment/secrets guidance](https://docs.docker.com/compose/how-tos/environment-variables/best-practices/).

## Stage 8 — Observability and measured performance

Goal: make correctness and latency diagnosable.

- [ ] Add request/analysis IDs and structured event fields across API, integrations, cache, features,
      rules, model, decisions, and persistence.
- [ ] Add readiness checks for Postgres/Redis separately from process liveness.
- [ ] Measure request count, error count, latency, provider latency, cache hit rate, POI count,
      candidate count, and phase timings without high-cardinality labels.
- [ ] Add traces across FastAPI, HTTPX, Redis, and SQLAlchemy only after log correlation is sound.
- [ ] Create a reproducible benchmark for point cache miss/hit and 25/100/400 candidate areas.
- [ ] Profile before optimizing; document baseline, change, hardware, dataset, and result.
- [ ] Define initial service objectives such as cached point p95 latency and successful-analysis rate.

Done when a slow or failed request can be explained from telemetry and performance claims include a
reproducible benchmark.

Read: [Prometheus instrumentation practices](https://prometheus.io/docs/practices/instrumentation/),
[OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/), and
[OpenTelemetry library instrumentation](https://opentelemetry.io/docs/languages/python/libraries/).

## Stage 9 — Build a legitimate dataset

Goal: create auditable supervision instead of manufacturing labels from the heuristic score.

- [ ] Write a data card describing the decision target, unit of observation, geography, time range,
      sources, licenses, intended use, exclusions, known bias, and refresh schedule.
- [ ] Choose an outcome/proxy that is available legally and does not merely restate baseline rules.
- [ ] Keep observation timestamps and compute features only from data available at that time.
- [ ] Store raw immutable snapshots, checksums, extraction code, schemas, and lineage.
- [ ] Check duplicates, coordinate errors, missingness, class/target distribution, temporal drift,
      spatial clustering, and leakage.
- [ ] Define district/city/time groups before looking at test results; freeze a final holdout.
- [ ] Version datasets and feature schemas; make one command reproduce the processed dataset.

Stop here if labels are not defensible. A transparent deterministic system is stronger portfolio work
than a trained model evaluated against invented outcomes.

## Stage 10 — Train and evaluate ML honestly

Goal: determine whether ML improves the real decision problem.

- [ ] Add separate training dependencies; keep scikit-learn/SHAP out of the serving image unless used.
- [ ] Train simple linear/logistic and tree baselines with pipelines and fixed seeds.
- [ ] Use geographic or temporal groups; never present a random nearby-point split as final evidence.
- [ ] Select metrics from the target: MAE/RMSE for regression, ROC-AUC plus precision/recall for
      classification, and NDCG/MAP/Precision@K for ranking.
- [ ] Compare every model with the deterministic baseline on exactly the same holdout.
- [ ] Report uncertainty, subgroup/geographic errors, calibration, failure cases, and negative results.
- [ ] Save artifact, dependency versions, code commit, data version, feature schema, metrics, and model
      card; verify loading and schema mismatch behavior.
- [ ] Implement the existing `LocationScoringModel` boundary and retain deterministic fallback.
- [ ] Add SHAP only after model validity; test that displayed contributions reconcile with output.

Done when a clean command reproduces evaluation, the final holdout stayed untouched during selection,
and deployment is justified by measurable improvement rather than plausible-looking scores.

Read: [scikit-learn metrics](https://scikit-learn.org/stable/api/sklearn.metrics.html),
[GroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html),
and [SHAP TreeExplainer](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html).

## Stage 11 — Background area analysis, only when measurements justify it

Goal: make large work reliable without prematurely splitting the modular monolith.

- [ ] Define an analysis state machine: pending, processing, completed, failed, cancelled, expired.
- [ ] Return `202` and a status URL; make retries idempotent and persist progress/error details.
- [ ] Add a Redis-backed worker only after a benchmark shows synchronous limits.
- [ ] Set job timeout, retry policy, concurrency, deduplication, cancellation, and dead-letter behavior.
- [ ] Ensure one area fetch is still shared by all candidates inside a job.
- [ ] Add worker integration tests and restart/recovery tests.

Read: [FastAPI background-task caveat](https://fastapi.tiangolo.com/tutorial/background-tasks/).
Heavy distributed jobs belong in a real queue/worker, not an in-process response callback.

## Stage 12 — Deployment and operations

Goal: run a secure, reproducible public demo.

- [ ] Pick one simple target and document why: a VM with Compose, or managed container + managed
      Postgres/Redis. Do not add Kubernetes for portfolio decoration.
- [ ] Create separate development and production Compose/configuration; use managed secrets.
- [ ] Add backend and frontend health checks, restart policy, migration release step, TLS, backups,
      restore test, retention policy, and rollback procedure.
- [ ] Publish versioned images from CI with vulnerability scan, SBOM, and immutable tag/digest.
- [ ] Add staging smoke tests and a post-deploy point-analysis check with controlled fixtures.
- [ ] Protect the public demo with budgets, quotas, provider-compliant traffic, and monitoring.
- [ ] Test a database restore and one application rollback before calling it production-ready.

Done when the demo survives a process restart, a migration deployment, and a documented rollback.

## Stage 13 — Portfolio presentation

Goal: let a reviewer understand the engineering in five minutes and inspect depth in thirty.

- [ ] Add a 60–90 second demo video and screenshots with OSM attribution.
- [ ] Put the problem, live demo, architecture, request/data flow, quick start, test status, and honest
      limitations above the README fold.
- [ ] Publish one architecture decision record each for modular monolith, deterministic-before-ML,
      PostGIS geography, shared area fetch, cache policy, and model validation strategy.
- [ ] Include a feature dictionary, data/model cards, spatial-validation report, benchmark report,
      threat model, runbook, and API examples.
- [ ] Show evidence in numbers: tests/coverage, cache hit improvement, p50/p95 latency, dataset size,
      holdout design, baseline-versus-model metrics, image size, and bundle change.
- [ ] Create a seeded/demo mode so reviewers are not blocked by a public provider outage.
- [ ] Label what is complete, experimental, and planned. Never claim users, accuracy, or scale that
      you did not measure.

## Recommended 14-week sequence

| Weeks | Deliverable |
| --- | --- |
| 1 | Baseline reproduction, code map, issues, Docker/database smoke test |
| 2–3 | Backend boundary refactor with characterization tests |
| 4 | Persistence and analysis-history APIs |
| 5 | PostGIS-native queries and spatial integration tests |
| 6 | External-provider resilience, policies, attribution, cache tests |
| 7 | Versioned business profiles and scoring sensitivity report |
| 8 | Frontend component refactor, API types, accessibility, end-to-end tests |
| 9 | Security limits, threat model, container hardening |
| 10 | Observability and reproducible performance benchmark |
| 11–12 | Dataset card/pipeline; stop or pivot if the data gate fails |
| 13 | ML evaluation only if data passed; otherwise deepen deterministic validation |
| 14 | Deployment, runbook, screenshots/video, final portfolio case study |

## Final release checklist

A `v1.0.0` portfolio release is ready only when:

- [ ] A fresh clone passes setup, checks, migrations, and smoke tests.
- [ ] Point and area workflows have unit, integration, and end-to-end coverage.
- [ ] PostGIS, Redis, provider failure, and cache behavior are tested with real services in CI.
- [ ] External-service policy, attribution, data provenance, and licenses are documented.
- [ ] Limits, security headers, dependency/image scans, secrets, backup, restore, and rollback are tested.
- [ ] Telemetry and benchmarks support every performance claim.
- [ ] Every score exposes evidence, feature/profile/model versions, rules, and confidence limitations.
- [ ] ML claims exist only if the data and spatial/temporal evaluation gates passed.
- [ ] A public demo, video fallback, architecture diagram, ADRs, and concise case study are available.

## Reference shelf

Prefer these primary sources over copy-pasted tutorials:

- Python/backend: [Python virtual environments](https://docs.python.org/3/library/venv.html),
  [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/),
  [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/),
  [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/),
  [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/),
  [HTTPX timeouts](https://www.python-httpx.org/advanced/timeouts/), and
  [HTTPX resource limits](https://www.python-httpx.org/advanced/resource-limits/).
- Database/geospatial: [SQLAlchemy 2 documentation](https://docs.sqlalchemy.org/en/20/),
  [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html),
  [GeoAlchemy2 documentation](https://geoalchemy-2.readthedocs.io/),
  [PostGIS reference](https://postgis.net/docs/), and
  [PostgreSQL `EXPLAIN`](https://www.postgresql.org/docs/current/using-explain.html).
- Tests/quality: [pytest fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html),
  [pytest monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html),
  [Ruff](https://docs.astral.sh/ruff/), [mypy](https://mypy.readthedocs.io/), and
  [pre-commit](https://pre-commit.com/).
- Frontend: [React Learn](https://react.dev/learn),
  [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro),
  [Vite guide](https://vite.dev/guide/), [Vitest guide](https://vitest.dev/guide/),
  [Testing Library principles](https://testing-library.com/docs/guiding-principles/),
  [Playwright](https://playwright.dev/docs/intro), and
  [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/).
- Operations/security: [Docker Compose](https://docs.docker.com/compose/),
  [GitHub Actions tutorials](https://docs.github.com/en/actions/tutorials),
  [OWASP API Security](https://owasp.org/API-Security/),
  [OpenTelemetry](https://opentelemetry.io/docs/), and
  [Prometheus practices](https://prometheus.io/docs/practices/instrumentation/).
- ML evidence: [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html),
  [cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html),
  [SHAP documentation](https://shap.readthedocs.io/), and
  [Google model cards](https://modelcards.withgoogle.com/about).
