"""Version metadata endpoint."""

from fastapi import APIRouter, status
from pydantic import BaseModel

from earthdata.core.di import SettingsDep

router = APIRouter(tags=["version"])


class VersionInfo(BaseModel):
    """Version metadata response body."""

    app_name: str
    version: str
    environment: str


@router.get(
    "/version",
    response_model=VersionInfo,
    status_code=status.HTTP_200_OK,
    summary="Application version and environment metadata",
)
async def get_version(settings: SettingsDep) -> VersionInfo:
    """Return the running application's name, version, and environment."""
    return VersionInfo(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )
