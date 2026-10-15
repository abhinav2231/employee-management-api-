import logging
import uuid
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: List[ErrorDetail] = []
    request_id: Optional[str] = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody
    detail: Optional[str] = None
    error_code: Optional[str] = None
    field: Optional[str] = None


class AppException(Exception):
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "BAD_REQUEST",
        field: Optional[str] = None,
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        self.field = field
        super().__init__(detail)


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found", field: Optional[str] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            field=field,
        )


class ConflictException(AppException):
    def __init__(self, detail: str = "Resource conflict", field: Optional[str] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            field=field,
        )


class BadRequestException(AppException):
    def __init__(self, detail: str = "Invalid request", field: Optional[str] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
            field=field,
        )


def _build_error_response(
    status_code: int,
    code: str,
    message: str,
    field: Optional[str] = None,
    request: Optional[Request] = None,
    details: Optional[List[Dict[str, Any]]] = None,
) -> JSONResponse:
    req_id = None
    if request:
        req_id = request.headers.get("x-request-id") or getattr(request.state, "request_id", None)
    if not req_id:
        req_id = f"req-{uuid.uuid4().hex[:12]}"

    if details is None:
        details = [{"field": field, "issue": message}] if field else []

    payload = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": req_id,
        },
        # Legacy/top-level compatibility fields
        "detail": message,
        "error_code": code,
        "field": field,
    }
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return _build_error_response(
            status_code=exc.status_code,
            code=exc.error_code,
            message=exc.detail,
            field=exc.field,
            request=request,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            404: "NOT_FOUND",
            400: "BAD_REQUEST",
            401: "UNAUTHENTICATED",
            403: "FORBIDDEN",
            409: "CONFLICT",
        }
        error_code = code_map.get(exc.status_code, "HTTP_ERROR")
        detail_msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return _build_error_response(
            status_code=exc.status_code,
            code=error_code,
            message=detail_msg,
            field=None,
            request=request,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        first_error = errors[0] if errors else {}
        loc = first_error.get("loc", [])
        field_name = str(loc[-1]) if loc else None
        msg = first_error.get("msg", "Validation error")
        if isinstance(msg, str):
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, "):]
            elif msg.startswith("Value error,"):
                msg = msg[len("Value error,"):].strip()

        all_details = []
        for err in errors:
            e_loc = err.get("loc", [])
            f_name = str(e_loc[-1]) if e_loc else None
            e_msg = err.get("msg", "Invalid value")
            if isinstance(e_msg, str):
                if e_msg.startswith("Value error, "):
                    e_msg = e_msg[len("Value error, "):]
                elif e_msg.startswith("Value error,"):
                    e_msg = e_msg[len("Value error,"):].strip()
            all_details.append({"field": f_name, "issue": e_msg})

        return _build_error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message=msg,
            field=field_name,
            request=request,
            details=all_details,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception: %s", exc)
        return _build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_ERROR",
            message="An internal server error occurred.",
            field=None,
            request=request,
        )
