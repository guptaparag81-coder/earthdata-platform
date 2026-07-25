"""Aggregate API v1 router."""

from fastapi import APIRouter

from earthdata.api.v1.endpoints import (
    analytics,
    dashboard,
    health,
    pipeline,
    processed_observations,
    raw_observations,
    version,
)

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(version.router)
api_v1_router.include_router(raw_observations.router)
api_v1_router.include_router(processed_observations.router)
api_v1_router.include_router(pipeline.router)
api_v1_router.include_router(analytics.router)
api_v1_router.include_router(dashboard.router)
