# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- **NASA EONET ingestion failure**: `categories[].id` is now `int | str`
  (was `int`-only) in both `EonetCategory` (`ingestion/schemas.py`) and
  `CleanedCategory` (`processing/validation.py`). EONET's live API returns
  string category slugs (e.g. `"wildfires"`, `"severeStorms"`) rather than
  the small integers the schemas previously required, which made every
  ingest fail Pydantic validation. `category.id` is never read downstream
  (only `category.title` is used), so the fix is a pure type widening with
  no behavior change; legacy integer ids continue to validate.

## [1.0.0] - 2026-07-25

### Added

- **Sprint 0 — Scaffold**: project structure, `pyproject.toml`, Ruff/Black/MyPy
  config, structured logging, environment-based settings, dependency
  injection wiring, Docker/Compose, Alembic, README.
- **Sprint 1 — Backend foundation**: async SQLAlchemy engine/session,
  ORM models, health/version endpoints, global exception handling, request
  logging middleware.
- **Sprint 2 — Ingestion**: async EONET HTTP client with retry/backoff,
  Pydantic response validation, `IngestionService` storing raw payloads.
- **Sprint 3 — Processing & storage**: cleaning/validation/transformation
  pipeline, repository pattern, `ProcessingService`, idempotent upsert into
  PostgreSQL.
- **Sprint 4 — REST API**: full CRUD for raw and processed observations with
  pagination, filtering, and sorting; pipeline trigger endpoints; OpenAPI
  documentation.
- **Sprint 5 — Visualisation**: summary statistics, time-series aggregation,
  JSON/CSV export, interactive HTML dashboard (Chart.js).
- **Sprint 6 — Testing**: unit, service, repository, database, API, and
  integration tests against a real ephemeral PostgreSQL database
  (`pytest-postgresql`); external API calls mocked with `respx`; 100% test
  coverage enforced via `--cov-fail-under=100`.
- **Sprint 7 — Docker & CI**: container/compose health checks, GitHub Actions
  CI running Ruff, Black, MyPy, Pytest, and a coverage report artifact.
- **Sprint 8 — Documentation**: installation guide, usage guide, API
  reference, architecture diagrams, contributing guide, license.

### Fixed

- `ProcessedObservationRepository.upsert` no longer inserts a `NULL` primary
  key and no longer returns stale ORM state on conflict (now refetches with
  `populate_existing=True`).
- `BaseRepository.update` now refreshes the instance after flush so
  server-computed `onupdate` columns (e.g. `updated_at`) are populated
  before the response is serialized.

[1.0.0]: https://github.com/guptaparag81-coder/earthdata-platform/releases/tag/v1.0.0
