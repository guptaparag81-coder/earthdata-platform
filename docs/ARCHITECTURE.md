# Architecture

## Layering

Requests flow strictly downward; no layer constructs its own collaborators —
everything is wired through FastAPI's `Depends` (`core/di.py`).

```mermaid
flowchart TD
    Client[HTTP Client] --> API[api/v1 — routers & endpoints]
    API --> Services[services — ingestion, processing, analytics]
    API --> Repos[repositories — repository pattern]
    Services --> Repos
    Repos --> DB[(PostgreSQL)]
    Services --> EONET[NASA EONET API]

    subgraph Cross-cutting
        Config[core/config — Settings]
        Logging[core/logging]
        Exceptions[core/exceptions]
        DI[core/di]
    end

    Config -.-> API
    Config -.-> Services
    Logging -.-> API
    Exceptions -.-> API
    DI -.-> API
```

CRUD endpoints with no business logic beyond persistence and 404 handling
(`raw-observations`, `processed-observations`) call repositories directly,
skipping the service layer — adding a pass-through service there would be an
abstraction with no purpose. Ingestion, processing, and analytics have real
orchestration logic and go through a service.

## Data flow: ingest → process → serve

```mermaid
sequenceDiagram
    participant U as Client
    participant API as FastAPI
    participant IS as IngestionService
    participant EONET as NASA EONET API
    participant RR as RawObservationRepository
    participant PS as ProcessingService
    participant PR as ProcessedObservationRepository
    participant DB as PostgreSQL

    U->>API: POST /pipeline/ingest
    API->>IS: ingest_events()
    IS->>EONET: GET /events (retried on 5xx/network errors)
    EONET-->>IS: events JSON
    IS->>IS: validate envelope (Pydantic)
    IS->>RR: bulk_add(raw records)
    RR->>DB: INSERT raw_observations
    IS-->>API: RawObservation[]
    API-->>U: 201 IngestResult

    U->>API: POST /pipeline/process
    API->>PS: process_pending()
    PS->>RR: list_unprocessed()
    RR->>DB: SELECT unprocessed raw rows
    loop each raw observation
        PS->>PS: clean → validate → transform
        alt valid
            PS->>PR: upsert(processed)
            PR->>DB: INSERT ... ON CONFLICT DO UPDATE
        else invalid
            PS->>PS: log + skip (does not abort batch)
        end
    end
    PS-->>API: ProcessedObservation[]
    API-->>U: 200 ProcessResult
```

## Database schema

```mermaid
erDiagram
    RAW_OBSERVATIONS ||--o{ PROCESSED_OBSERVATIONS : "processed into"
    RAW_OBSERVATIONS {
        uuid id PK
        string source
        string external_id
        jsonb payload
        timestamptz fetched_at
        timestamptz created_at
    }
    PROCESSED_OBSERVATIONS {
        uuid id PK
        uuid raw_observation_id FK
        string external_id UK
        string title
        string category
        string source
        timestamptz event_date
        float latitude
        float longitude
        bool is_open
        timestamptz created_at
        timestamptz updated_at
    }
```

