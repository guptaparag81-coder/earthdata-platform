"""Direct unit tests for the global exception handlers."""

import json
from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import Response

from earthdata.core.exceptions import (
    DataValidationError,
    EarthDataError,
    RecordNotFoundError,
    UpstreamServiceError,
    register_exception_handlers,
)


def _make_request(path: str = "/test") -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "raw_path": path.encode(),
        "headers": [],
        "query_string": b"",
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("testclient", 123),
    }
    return Request(scope)


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    return app


async def _call(
    handler: Callable[[Request, Exception], Response | Awaitable[Response]],
    request: Request,
    exc: Exception,
) -> Response:
    result = handler(request, exc)
    if isinstance(result, Response):
        return result
    return await result


async def test_handle_earthdata_error_returns_upstream_status_and_code() -> None:
    app = _build_app()
    handler = app.exception_handlers[EarthDataError]

    response = await _call(handler, _make_request(), UpstreamServiceError("upstream down"))

    assert response.status_code == 502
    body = json.loads(bytes(response.body))
    assert body["error"]["code"] == "upstream_service_error"
    assert body["error"]["message"] == "upstream down"


async def test_handle_earthdata_error_returns_404_for_record_not_found() -> None:
    app = _build_app()
    handler = app.exception_handlers[EarthDataError]

    response = await _call(handler, _make_request(), RecordNotFoundError("not found"))

    assert response.status_code == 404
    body = json.loads(bytes(response.body))
    assert body["error"]["code"] == "record_not_found"


async def test_handle_earthdata_error_returns_422_for_data_validation_error() -> None:
    app = _build_app()
    handler = app.exception_handlers[EarthDataError]

    response = await _call(
        handler, _make_request(), DataValidationError("bad data", details={"errors": ["x"]})
    )

    assert response.status_code == 422
    body = json.loads(bytes(response.body))
    assert body["error"]["code"] == "data_validation_error"
    assert body["error"]["details"] == {"errors": ["x"]}


async def test_handle_request_validation_error() -> None:
    app = _build_app()
    handler = app.exception_handlers[RequestValidationError]

    exc = RequestValidationError(errors=[])
    response = await _call(handler, _make_request(), exc)

    assert response.status_code == 422
    body = json.loads(bytes(response.body))
    assert body["error"]["code"] == "request_validation_error"


async def test_handle_http_exception() -> None:
    app = _build_app()
    handler = app.exception_handlers[StarletteHTTPException]

    exc = StarletteHTTPException(status_code=404, detail="Not Found")
    response = await _call(handler, _make_request(), exc)

    assert response.status_code == 404
    body = json.loads(bytes(response.body))
    assert body["error"]["code"] == "http_error"
    assert body["error"]["message"] == "Not Found"


async def test_handle_unexpected_error_returns_500() -> None:
    app = _build_app()
    handler = app.exception_handlers[Exception]

    response = await _call(handler, _make_request(), ValueError("boom"))

    assert response.status_code == 500
    body = json.loads(bytes(response.body))
    assert body["error"]["code"] == "internal_error"
