"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized, typed application settings.

    All values are sourced from environment variables (or a `.env` file in
    local development) and validated at process startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
    )

    # Application
    app_name: str = "EarthData"
    app_env: Literal["local", "test", "staging", "production"] = "local"
    app_debug: bool = False
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"

    # Logging
    log_level: str = "INFO"
    log_json: bool = False

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://earthdata:earthdata@localhost:5432/earthdata"
    )
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Earth observation source (NASA EONET)
    eonet_base_url: str = "https://eonet.gsfc.nasa.gov/api/v3"
    eonet_timeout_seconds: float = 10.0
    eonet_max_retries: int = 3


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached `Settings` instance."""
    return Settings()
