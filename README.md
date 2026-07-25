# EarthData

[![CI](https://github.com/guptaparag81-coder/earthdata-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/guptaparag81-coder/earthdata-platform/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/guptaparag81-coder/earthdata-platform/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

Earth observation data ingestion and processing platform. Fetches natural
event data from NASA's public [EONET](https://eonet.gsfc.nasa.gov/) API (no
API key required), validates and stores the raw responses, cleans/validates/
transforms them into structured PostgreSQL records, and exposes them through
a REST API plus an analytics/visualisation layer.

## Contents

- [Stack](#stack)
- [Architecture](#architecture)
- [Getting started](#getting-started)
- [Endpoints](#endpoints)
- [Development](#development)
- [Migrations](#migrations)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Stack

- Python 3.13, FastAPI, Pydantic v2 / Pydantic Settings
- SQLAlchemy 2.x (async) + Alembic
- PostgreSQL, asyncpg
- Ruff, Black, MyPy (strict), Pytest (100% coverage gate)
- Docker / Docker Compose, GitHub Actions CI

## Architecture

```
src/earthdata/
├── main.py                # FastAPI app factory
├── core/                   # config, logging, DI wiring, exceptions
├── db/                     # engine/session, ORM models
├── api/v1/                 # routers, endpoints (health, version, CRUD, pipeline, analytics, dashboard)
├── middleware/             # request logging middleware
├── ingestion/              # EONET client, schemas, ingestion service
├── processing/             # cleaning, validation, transformation, processing service
├── repositories/           # repository pattern over SQLAlchemy
├── analytics/              # summary stats, time-series aggregation, CSV export
└── schemas/                # API-facing Pydantic request/response models
```

Layering: `api` -> `services` (`ingestion`/`processing`/`analytics`) ->
`repositories` -> `db`. Dependencies are injected via FastAPI's `Depends`
(see `core/di.py`); no layer constructs its own collaborators. CRUD endpoints
call repositories directly (no service layer) since there is no business
logic beyond persistence and 404 handling.

Diagrams (component layering, ingest/process sequence, ER diagram):
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Getting started

### Local (Docker)

```bash
cp .env.example .env
docker compose up --build
```

API available at `http://localhost:8000`. Apply migrations once the `db`
service is healthy:

```bash
docker compose exec api alembic upgrade head
```

### Local (without Docker)

Requires a running PostgreSQL instance matching `DATABASE_URL` in `.env`.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn earthdata.main:app --reload
```

Full walkthrough, environment variables, verification steps:
[docs/INSTALLATION.md](docs/INSTALLATION.md). End-to-end usage examples
(ingest, process, query, export, dashboard):
[docs/USAGE.md](docs/USAGE.md).

## Endpoints

| Method                 | Path                                     | Description                                   |
| ---------------------- | ----------------------------------------- | ---------------------------------------------- |
| GET                     | `/api/v1/health`                          | Liveness + database connectivity               |
| GET                     | `/api/v1/version`                         | App name, version, environment                 |
| GET/POST/DELETE         | `/api/v1/raw-observations[/{id}]`         | Raw EONET payloads (list/get/create/delete)    |
| GET/POST/PATCH/DELETE   | `/api/v1/processed-observations[/{id}]`   | Processed events (full CRUD)                   |
| POST                    | `/api/v1/pipeline/ingest`                 | Fetch events from EONET, store raw             |
| POST                    | `/api/v1/pipeline/process`                | Clean/validate/transform pending raw records   |
| GET                     | `/api/v1/analytics/summary`               | Aggregate counts, category/source breakdowns  |
| GET                     | `/api/v1/analytics/timeseries`            | Event counts bucketed by day/week/month        |
| GET                     | `/api/v1/analytics/export`                | Export processed data as JSON or CSV           |
| GET                     | `/api/v1/dashboard`                       | Interactive HTML dashboard (Chart.js)          |

List endpoints (`raw-observations`, `processed-observations`) support
pagination (`limit`/`offset`), filtering (e.g. `source`, `category`,
`is_open`, date ranges), and sorting (`sort_by`/`sort_order`). Full field-level
reference: [docs/API.md](docs/API.md); interactive schema at `/docs`
(Swagger UI) and `/redoc`.

## Development

```bash
ruff check .
black --check .
mypy .
pytest   # spins up an ephemeral PostgreSQL DB per test via pytest-postgresql; 100% coverage enforced
```

CI (`.github/workflows/ci.yml`) runs the same checks on every push/PR,
plus a Docker image build, and uploads the HTML/XML coverage report as a
build artifact.

## Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Documentation

- [Installation guide](docs/INSTALLATION.md)
- [Usage guide](docs/USAGE.md)
- [API reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Changelog](CHANGELOG.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, code style, and the
pre-PR checklist.

## License

[MIT](LICENSE)
