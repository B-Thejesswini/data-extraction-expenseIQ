import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from data_extraction_project.core.exceptions import (
    HTTP_STATUS_CODES,
    AppError,
    InternalError,
    InvalidRequestError,
)
from data_extraction_project.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)

DEFAULT_HTTP_ERROR_CODE = "HTTP_ERROR"


def _respond(
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(code=code, message=message)
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


def _from_app_error(exc: AppError) -> JSONResponse:
    return _respond(exc.status_code, exc.code, exc.message)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _from_app_error(exc)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Framework errors (404, 405, ...): code from the status map, message from the framework."""
    code = HTTP_STATUS_CODES.get(str(exc.status_code), DEFAULT_HTTP_ERROR_CODE)
    return _respond(exc.status_code, code, str(exc.detail), headers=exc.headers)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = "; ".join(
        f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}"
        for err in exc.errors()
    )
    return _from_app_error(InvalidRequestError(details=details))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return _from_app_error(InternalError())


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)