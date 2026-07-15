import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.errors.models import (
    APIError,
    ErrorBody,
    ErrorCode,
    ErrorEnvelope,
    RequestBodyTooLargeError,
)
from app.api.middleware.request_context import get_request_id
from app.application.errors import (
    AIServiceInvalidOutputError,
    AIServiceTimeoutError,
    AIServiceUnavailableError,
    DeviceRoleNotAllowedError,
    DuplicateRequestError,
    IdentityScopeMismatchError,
)

logger = logging.getLogger("aire.backend")


def _error_response(
    *,
    status_code: int,
    code: ErrorCode,
    message: str,
    retryable: bool,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    envelope = ErrorEnvelope(
        request_id=get_request_id(),
        error=ErrorBody(
            code=code,
            message=message,
            retryable=retryable,
            details=details or {},
        ),
    )
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(mode="json"),
    )


def register_error_handlers(app: FastAPI) -> None:
    application_errors = {
        DuplicateRequestError: (
            409,
            ErrorCode.DUPLICATE_REQUEST,
            "The request ID was already used with different content.",
            False,
        ),
        IdentityScopeMismatchError: (
            403,
            ErrorCode.IDENTITY_CLAIM_MISMATCH,
            "Requested identity scope does not match the authenticated device.",
            False,
        ),
        DeviceRoleNotAllowedError: (
            403,
            ErrorCode.UNAUTHORIZED_DEVICE,
            "Device role is not allowed for this interaction mode.",
            False,
        ),
        AIServiceUnavailableError: (
            503,
            ErrorCode.AI_SERVICE_UNAVAILABLE,
            "AI service is currently unavailable.",
            True,
        ),
        AIServiceTimeoutError: (
            504,
            ErrorCode.AI_SERVICE_TIMEOUT,
            "AI service exceeded the configured timeout.",
            True,
        ),
        AIServiceInvalidOutputError: (
            503,
            ErrorCode.AI_SERVICE_INVALID_OUTPUT,
            "AI service returned invalid structured output.",
            True,
        ),
    }

    async def handle_application_error(
        _request: Request,
        error: Exception,
    ) -> JSONResponse:
        status_code, code, message, retryable = application_errors[type(error)]
        return _error_response(
            status_code=status_code,
            code=code,
            message=message,
            retryable=retryable,
        )

    for error_class in application_errors:
        app.add_exception_handler(error_class, handle_application_error)

    @app.exception_handler(APIError)
    async def handle_api_error(_request: Request, error: APIError) -> JSONResponse:
        return _error_response(
            status_code=error.status_code,
            code=error.code,
            message=error.message,
            retryable=error.retryable,
            details=error.details,
        )

    @app.exception_handler(RequestBodyTooLargeError)
    async def handle_large_body(
        _request: Request,
        _error: RequestBodyTooLargeError,
    ) -> JSONResponse:
        return _error_response(
            status_code=413,
            code=ErrorCode.REQUEST_TOO_LARGE,
            message="Request body exceeds the configured size limit.",
            retryable=False,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        issues = [
            {
                "location": ".".join(str(part) for part in issue["loc"]),
                "type": issue["type"],
            }
            for issue in error.errors()
        ]
        return _error_response(
            status_code=400,
            code=ErrorCode.INVALID_REQUEST,
            message="Request validation failed.",
            retryable=False,
            details={"issues": issues[:16]},
        )

    @app.exception_handler(HTTPException)
    async def handle_http_error(
        _request: Request,
        error: HTTPException,
    ) -> JSONResponse:
        code = (
            ErrorCode.UNAUTHORIZED_DEVICE
            if error.status_code == 401
            else ErrorCode.INVALID_REQUEST
        )
        return _error_response(
            status_code=error.status_code,
            code=code,
            message="HTTP request could not be processed.",
            retryable=False,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        _request: Request,
        error: Exception,
    ) -> JSONResponse:
        logger.error(
            "unhandled_request_error",
            extra={
                "event": "unhandled_request_error",
                "request_id": get_request_id(),
                "error_type": type(error).__name__,
            },
        )
        return _error_response(
            status_code=500,
            code=ErrorCode.INTERNAL_ERROR,
            message="An internal server error occurred.",
            retryable=True,
        )
