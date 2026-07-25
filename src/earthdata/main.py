"""FastAPI application entrypoint and factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from earthdata.api.v1.router import api_v1_router
from earthdata.core.config import get_settings
from earthdata.core.exceptions import register_exception_handlers
from earthdata.core.logging import configure_logging, get_logger
from earthdata.middleware.logging import RequestLoggingMiddleware

logger = get_logger(__name__)

OPENAPI_TAGS = [
    {"name": "health", "description": "Liveness and readiness checks."},
    {"name": "version", "description": "Application version metadata."},
    {"name": "raw-observations", "description": "CRUD access to raw ingested EONET payloads."},
    {
        "name": "processed-observations",
        "description": "CRUD access to cleaned, validated Earth observation events.",
    },
    {"name": "pipeline", "description": "Trigger on-demand ingestion and processing runs."},
    {"name": "analytics", "description": "Summary statistics, time-series data, and exports."},
    {"name": "dashboard", "description": "Interactive HTML visualisation dashboard."},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application startup/shutdown hooks."""
    settings = get_settings()
    configure_logging(settings)
    logger.info("application_startup", extra={"environment": settings.app_env})
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
        lifespan=lifespan,
        openapi_tags=OPENAPI_TAGS,
    )

    app.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(app)
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
