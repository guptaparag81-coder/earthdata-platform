"""Async HTTP client for the NASA EONET Earth observation API."""

from __future__ import annotations

from types import TracebackType
from typing import Any, Self

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from earthdata.core.exceptions import UpstreamServiceError
from earthdata.core.logging import get_logger

logger = get_logger(__name__)

_RETRYABLE_EXCEPTIONS = (httpx.TransportError, httpx.HTTPStatusError)


def _is_retryable(exc: BaseException) -> bool:
    """Retry on network errors and 5xx responses only; 4xx errors are not retried."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, httpx.TransportError)


class EonetClient:
    """Thin async client over the public NASA EONET REST API.

    No API key is required. Requests are retried with exponential backoff
    on transient network failures and 5xx responses.
    """

    def __init__(self, base_url: str, timeout_seconds: float, max_retries: int) -> None:
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._http_client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout_seconds)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._http_client.aclose()

    async def fetch_events(
        self,
        *,
        status: str = "open",
        limit: int = 50,
        days: int | None = None,
    ) -> dict[str, Any]:
        """Fetch natural events from EONET.

        Args:
            status: Event status filter (`open`, `closed`, or `all`).
            limit: Maximum number of events to return.
            days: If given, restrict results to events from the last N days.

        Returns:
            The raw decoded JSON response.

        Raises:
            UpstreamServiceError: If the request ultimately fails after retries.
        """
        params: dict[str, str | int] = {"status": status, "limit": limit}
        if days is not None:
            params["days"] = days

        return await self._get_with_retry("/events", params=params)

    async def _get_with_retry(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        retrying = retry(
            reraise=True,
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
            retry=retry_if_exception(_is_retryable),
        )
        try:
            return await retrying(self._get)(path, params)
        except _RETRYABLE_EXCEPTIONS as exc:
            logger.error("eonet_request_failed", extra={"path": path, "error": str(exc)})
            raise UpstreamServiceError(
                f"EONET request to {path} failed after {self._max_retries} attempts.",
                details={"path": path},
            ) from exc

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = await self._http_client.get(path, params=params)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result
