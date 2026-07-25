"""Health check endpoint."""

from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text

from earthdata.core.di import DbSessionDep

router = APIRouter(tags=["health"])


class HealthStatus(BaseModel):
    """Health check response body."""

    status: str
    database: str


@router.get(
    "/health",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Liveness and database connectivity check",
)
async def get_health(session: DbSessionDep) -> HealthStatus:
    """Report service liveness and database connectivity."""
    database_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"

    return HealthStatus(status="ok", database=database_status)
