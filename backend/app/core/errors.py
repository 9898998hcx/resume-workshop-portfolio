from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Any | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def _error_payload(code: str, message: str, details: Any | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"error": error}


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        content=_error_payload(exc.code, exc.message, exc.details),
        status_code=exc.status_code,
    )


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        422,
        _error_payload("VALIDATION_ERROR", "请求参数不合法", exc.errors()),
    )


async def unexpected_error_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        content=_error_payload("INTERNAL_ERROR", "服务暂时不可用"),
        status_code=500,
    )
