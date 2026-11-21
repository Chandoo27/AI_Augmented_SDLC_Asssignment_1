from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.models import ErrorCode, ErrorDetail, ErrorResponse
from src.routes import router
from src.storage import JsonTaskStore, PersistenceError, TaskNotFound

logger = logging.getLogger(__name__)


def _error_response(
    status_code: int,
    code: ErrorCode,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(code=code, message=message, details=details or [])
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def _validation_details(error: RequestValidationError) -> list[ErrorDetail]:
    details: list[ErrorDetail] = []
    for item in error.errors():
        location = ".".join(
            str(part) for part in item["loc"] if part not in {"body", "query", "path"}
        )
        message = item["msg"]
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        details.append(ErrorDetail(field=location or "request", message=message))
    return details


def create_app(data_file: Path | None = None) -> FastAPI:
    configured_path = data_file or Path(os.environ.get("SMART_TODO_DATA_FILE", "data/tasks.json"))
    application = FastAPI(title="Smart Todo API", version="1.0.0")
    application.state.store = JsonTaskStore(configured_path)
    application.include_router(router)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            status_code=422,
            code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed",
            details=_validation_details(error),
        )

    @application.exception_handler(TaskNotFound)
    async def task_not_found_handler(request: Request, error: TaskNotFound) -> JSONResponse:
        return _error_response(
            status_code=404,
            code=ErrorCode.TASK_NOT_FOUND,
            message="Task not found",
        )

    @application.exception_handler(PersistenceError)
    async def persistence_error_handler(request: Request, error: PersistenceError) -> JSONResponse:
        return _error_response(
            status_code=500,
            code=ErrorCode.DATA_FILE_ERROR,
            message="Task data is unavailable",
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, error: StarletteHTTPException) -> JSONResponse:
        is_not_found = error.status_code == 404
        return _error_response(
            status_code=error.status_code,
            code=ErrorCode.NOT_FOUND if is_not_found else ErrorCode.HTTP_ERROR,
            message="Not found" if is_not_found else "HTTP request failed",
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, error: Exception) -> JSONResponse:
        logger.error(
            "Unhandled request error",
            exc_info=(type(error), error, error.__traceback__),
        )
        return _error_response(
            status_code=500,
            code=ErrorCode.INTERNAL_ERROR,
            message="An internal error occurred",
        )

    return application


app = create_app()
