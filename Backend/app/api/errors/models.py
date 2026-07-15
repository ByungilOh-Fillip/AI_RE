from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorCode(StrEnum):
    INVALID_REQUEST = "InvalidRequest"
    UNSUPPORTED_SCHEMA_VERSION = "UnsupportedSchemaVersion"
    UNAUTHORIZED_DEVICE = "UnauthorizedDevice"
    IDENTITY_CLAIM_MISMATCH = "IdentityClaimMismatch"
    DUPLICATE_REQUEST = "DuplicateRequest"
    REQUEST_TOO_LARGE = "RequestTooLarge"
    REQUEST_TIMEOUT = "RequestTimeout"
    AUTHENTICATION_UNAVAILABLE = "AuthenticationUnavailable"
    AI_SERVICE_UNAVAILABLE = "AIServiceUnavailable"
    AI_SERVICE_TIMEOUT = "AIServiceTimeout"
    AI_SERVICE_INVALID_OUTPUT = "AIServiceInvalidOutput"
    INTERNAL_ERROR = "InternalError"


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ErrorCode
    message: str = Field(min_length=1, max_length=512)
    retryable: bool
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    request_id: str
    error: ErrorBody


class APIError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: ErrorCode,
        message: str,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code.value)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}


class RequestBodyTooLargeError(Exception):
    pass
