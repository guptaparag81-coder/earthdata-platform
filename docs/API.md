# API Documentation

Interactive, always-up-to-date reference: **Swagger UI** at `/docs`, **ReDoc**
at `/redoc`, raw schema at `/openapi.json`. This document is a stable summary;
request/response field types and validation constraints live in the OpenAPI
schema itself.

All routes are prefixed with `API_V1_PREFIX` (default `/api/v1`). Errors use
a single envelope:

```json
{ "error": { "code": "record_not_found", "message": "...", "details": {} } }
```

| HTTP status | `error.code` | Cause |
| --- | --- | --- |
| 404 | `record_not_found` | No record with that id |
| 422 | `request_validation_error` | Request body/query failed schema validation |
| 422 | `data_validation_error` | Upstream/domain data failed validation |
| 502 | `upstream_service_error` | EONET request failed after retries |
| 500 | `internal_error` | Unhandled server error |

## Health & version

| Method | Path | Response |
| --- | --- | --- |
| GET | `/health` | `{"status": "ok", "database": "ok"\|"unavailable"}` |
| GET | `/version` | `{"app_name", "version", "environment"}` |

## Raw observations

| Method | Path | Description |
| --- | --- | --- |
| GET | `/raw-observations` | List (pagination + filtering + sorting) |
| GET | `/raw-observations/{id}` | Get by id (404 if missing) |
| POST | `/raw-observations` | Create (manual backfill) |
| DELETE | `/raw-observations/{id}` | Delete |

Query params for list: `limit` (1-500, default 50), `offset`, `source`,
`external_id`, `fetched_after`, `fetched_before`, `sort_by`
(`created_at`\|`fetched_at`\|`source`\|`external_id`), `sort_order`
(`asc`\|`desc`).

## Processed observations

| Method | Path | Description |
| --- | --- | --- |
| GET | `/processed-observations` | List (pagination + filtering + sorting) |
| GET | `/processed-observations/{id}` | Get by id |
| POST | `/processed-observations` | Create |
| PATCH | `/processed-observations/{id}` | Partial update |
| DELETE | `/processed-observations/{id}` | Delete |

Query params for list: `limit`, `offset`, `category`, `source`, `is_open`,
`external_id`, `event_after`, `event_before`, `sort_by`
(`created_at`\|`updated_at`\|`event_date`\|`title`\|`category`\|`source`\|`external_id`),
`sort_order`.

List responses use the pagination envelope:

```json
{ "items": [...], "total": 0, "limit": 50, "offset": 0, "has_more": false }
```

## Pipeline

| Method | Path | Description |
| --- | --- | --- |
| POST | `/pipeline/ingest` | Fetch EONET events, store raw. Params: `status`, `limit`, `days` |
| POST | `/pipeline/process` | Process pending raw observations. Params: `limit` |

## Analytics

| Method | Path | Description |
| --- | --- | --- |
| GET | `/analytics/summary` | Totals, open/closed, by-category, by-source, event date bounds |
| GET | `/analytics/timeseries` | Bucketed counts. Params: `interval` (`day`\|`week`\|`month`), `start`, `end`, `category`, `source` |
| GET | `/analytics/export` | Export matching records. Params: `format` (`json`\|`csv`), plus the processed-observation filters, `limit` (default 1000, max 10000) |

CSV export returns `text/csv` with a `Content-Disposition: attachment`
header; JSON export returns a plain array of processed-observation objects.

## Dashboard

| Method | Path | Description |
| --- | --- | --- |
| GET | `/dashboard` | Interactive HTML dashboard (Chart.js, fetches the analytics endpoints client-side) |
