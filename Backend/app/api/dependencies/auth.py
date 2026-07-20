from datetime import datetime, timezone
from secrets import compare_digest
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.api.dependencies.database import DatabaseSession
from app.api.errors.models import APIError, ErrorCode
from app.domain.identity import AuthenticatedDevice, DeviceRole
from app.infrastructure.database.models import DeviceModel
from app.infrastructure.security.credentials import (
    CredentialProtectionNotConfiguredError,
    CredentialProtector,
)
from app.settings import Settings, get_settings

device_bearer = HTTPBearer(auto_error=False)


def _require_credentials(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if credentials is None:
        raise APIError(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED_DEVICE,
            message="Device bearer token is required.",
        )
    return credentials.credentials


def _protector(settings: Settings) -> CredentialProtector:
    try:
        return CredentialProtector(settings.device_credential_pepper)
    except CredentialProtectionNotConfiguredError as error:
        raise APIError(
            status_code=503,
            code=ErrorCode.AUTHENTICATION_UNAVAILABLE,
            message="Persistent device authentication is not configured.",
        ) from error


async def get_authenticated_device(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(device_bearer),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
    session: DatabaseSession,
) -> AuthenticatedDevice:
    token = _require_credentials(credentials)
    protector = _protector(settings)
    lookup_id = token.split(".", maxsplit=1)[0]
    result = await session.execute(
        select(DeviceModel).where(DeviceModel.token_lookup_id == lookup_id)
    )
    device = result.scalar_one_or_none()
    expected_hash = device.token_hash if device is not None else "0" * 64
    is_valid = protector.verify("device-token", token, expected_hash)
    if device is None or not is_valid or device.revoked_at is not None:
        raise APIError(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED_DEVICE,
            message="Device bearer token is invalid.",
        )

    device.last_used_at = datetime.now(timezone.utc)
    await session.commit()
    return AuthenticatedDevice(
        profile_id=device.profile_id,
        device_id=device.device_id,
        role=DeviceRole(device.role),
    )


def get_bootstrap_game_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(device_bearer),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    supplied = _require_credentials(credentials)
    configured = (
        settings.dev_game_device_token.get_secret_value()
        if settings.dev_game_device_token is not None
        else ""
    )
    if not configured:
        raise APIError(
            status_code=503,
            code=ErrorCode.AUTHENTICATION_UNAVAILABLE,
            message="GameClient bootstrap authentication is not configured.",
        )
    if not compare_digest(supplied, configured):
        raise APIError(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED_DEVICE,
            message="Bootstrap bearer token is invalid.",
        )
    return supplied


def get_credential_protector(
    settings: Annotated[Settings, Depends(get_settings)],
) -> CredentialProtector:
    return _protector(settings)
