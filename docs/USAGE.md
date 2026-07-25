# Usage Guide

Assumes the API is running at `http://localhost:8000` (see
[INSTALLATION.md](INSTALLATION.md)).

## 1. Ingest data from NASA EONET

Fetch open natural events and store the raw payloads:

```bash
curl -X POST "http://localhost:8000/api/v1/pipeline/ingest?status=open&limit=50"
```

```json
{
  "ingested_count": 12,
  "observations": [{ "id": "...", "source": "eonet", "external_id": "EONET_...", "...": "..." }]
}
```

Optional query params: `status` (`open`/`closed`/`all`), `limit` (1-500),
`days` (restrict to the last N days).

## 2. Process raw observations into structured records

```bash
curl -X POST "http://localhost:8000/api/v1/pipeline/process?limit=100"
```

Cleans, validates, and transforms pending raw records. Records that fail
validation (e.g. out-of-range coordinates) are skipped and logged — one bad
record does not abort the batch.

## 3. Query processed observations

List, filter, sort, paginate:

```bash
curl "http://localhost:8000/api/v1/processed-observations?category=Wildfires&is_open=true&sort_by=event_date&sort_order=desc&limit=20"
```

```json
{
  "items": [ { "id": "...", "external_id": "EONET_...", "category": "Wildfires", "...": "..." } ],
  "total": 42,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

Supported filters: `category`, `source`, `is_open`, `external_id`,
`event_after`, `event_before`. Sortable fields: `created_at`, `updated_at`,
`event_date`, `title`, `category`, `source`, `external_id`.

Fetch, update, or delete a single record:

```bash
curl "http://localhost:8000/api/v1/processed-observations/{id}"
curl -X PATCH "http://localhost:8000/api/v1/processed-observations/{id}" \
     -H "Content-Type: application/json" -d '{"is_open": false}'
curl -X DELETE "http://localhost:8000/api/v1/processed-observations/{id}"
```

## 4. Analytics

```bash
curl "http://localhost:8000/api/v1/analytics/summary"
curl "http://localhost:8000/api/v1/analytics/timeseries?interval=week&category=Wildfires"
```

## 5. Export data

```bash
curl "http://localhost:8000/api/v1/analytics/export?format=json&category=Wildfires" 
curl "http://localhost:8000/api/v1/analytics/export?format=csv" -o observations.csv
```

## 6. Dashboard

Open `http://localhost:8000/api/v1/dashboard` in a browser for an
interactive view: total/open/closed tiles, a category bar chart, and a
day/week/month time-series line chart.

## Typical workflow

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/ingest
curl -X POST http://localhost:8000/api/v1/pipeline/process
open http://localhost:8000/api/v1/dashboard   # macOS; use xdg-open on Linux
```

## Automating ingestion

There is no built-in scheduler. Run `pipeline/ingest` then `pipeline/process`
on a schedule via your platform's own tooling — e.g. a `cron` job hitting the
two endpoints with `curl`, or a Kubernetes `CronJob`.
