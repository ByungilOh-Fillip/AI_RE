from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.identity import AuthenticatedDevice
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device bearer token is required.",
        )

    authenticator = DevelopmentDeviceAuthenticator(settings)
    try:
        return authenticator.authenticate(credentials.credentials)
    except DevelopmentAuthenticationNotConfiguredError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Development authentication is not configured.",
        ) from error
    except InvalidDeviceTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device bearer token is invalid.",
        ) from error
