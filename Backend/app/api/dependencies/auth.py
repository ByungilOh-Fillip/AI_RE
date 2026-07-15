from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.identity import AuthenticatedDevice
from app.api.errors.models import APIError, ErrorCode
from app.infrastructure.security.development_authenticator import (
    DevelopmentAuthenticationNotConfiguredError,
    DevelopmentDeviceAuthenticator,
    InvalidDeviceTokenError,
)
from app.settings import Settings, get_settings

device_bearer = HTTPBearer(auto_error=False)


def get_authenticated_device(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(device_bearer),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedDevice:
    if credentials is None:
        raise APIError(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED_DEVICE,
            message="Device bearer token is required.",
        )

    authenticator = DevelopmentDeviceAuthenticator(settings)
    try:
        return authenticator.authenticate(credentials.credentials)
    except DevelopmentAuthenticationNotConfiguredError as error:
        raise APIError(
            status_code=503,
            code=ErrorCode.AUTHENTICATION_UNAVAILABLE,
            message="Development authentication is not configured.",
            retryable=False,
        ) from error
    except InvalidDeviceTokenError as error:
        raise APIError(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED_DEVICE,
            message="Device bearer token is invalid.",
        ) from error
