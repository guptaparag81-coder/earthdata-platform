# Installation Guide

## Prerequisites

| Requirement | Version | Needed for |
| --- | --- | --- |
| Python | 3.13 | local (non-Docker) runs |
| Docker + Docker Compose | recent | containerized runs |
| PostgreSQL client tools (`initdb`, `pg_ctl`, `postgres`) | 16.x | running the test suite |

## Option A — Docker (recommended)

```bash
git clone https://github.com/guptaparag81-coder/earthdata-platform.git
cd earthdata-platform
cp .env.example .env
docker compose up --build
```

This starts `db` (PostgreSQL 16) and `api` (the FastAPI app). Once `db`
reports healthy, apply migrations:

```bash
docker compose exec api alembic upgrade head
```

The API is now available at `http://localhost:8000`:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Dashboard: `http://localhost:8000/api/v1/dashboard`

Stop everything with `docker compose down` (add `-v` to also drop the
database volume).

## Option B — Local Python environment

Requires a running PostgreSQL instance reachable at the `DATABASE_URL` you
configure below.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` and point `DATABASE_URL` at your PostgreSQL instance, e.g.:

```
DATABASE_URL=postgresql+asyncpg://earthdata:earthdata@localhost:5432/earthdata
```

Create the database, apply migrations, and run the app:

```bash
createdb earthdata          # or: psql -c "CREATE DATABASE earthdata;"
alembic upgrade head
uvicorn earthdata.main:app --reload
```

## Environment variables

All settings are read from `.env` (see `.env.example` for the full list and
defaults) via `earthdata.core.config.Settings`:

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `EarthData` | Displayed in `/api/v1/version` and OpenAPI title |
| `APP_ENV` | `local` | `local`, `test`, `staging`, or `production` |
| `APP_DEBUG` | `true` | Enables FastAPI debug mode |
| `API_V1_PREFIX` | `/api/v1` | Base path for all versioned routes |
| `LOG_LEVEL` | `INFO` | Root logger level |
| `LOG_JSON` | `false` | Structured JSON logs (recommended for production) |
| `DATABASE_URL` | `postgresql+asyncpg://earthdata:earthdata@localhost:5432/earthdata` | Async SQLAlchemy DSN |
| `DATABASE_ECHO` | `false` | Log all SQL statements |
| `DATABASE_POOL_SIZE` / `DATABASE_MAX_OVERFLOW` | `5` / `10` | Connection pool sizing |
| `EONET_BASE_URL` | `https://eonet.gsfc.nasa.gov/api/v3` | No API key required |
| `EONET_TIMEOUT_SECONDS` | `10` | Per-request timeout |
| `EONET_MAX_RETRIES` | `3` | Retries on 5xx/network errors only |

## Verifying the install

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","database":"ok"}
```

## Running the test suite

```bash
pip install -e ".[dev]"
pytest
```

No Docker or manually-started PostgreSQL server is required for tests — a
throwaway PostgreSQL cluster is created per test via `pytest-postgresql`
using your local `initdb`/`pg_ctl` binaries.
