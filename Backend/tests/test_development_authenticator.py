import pytest
from pydantic import SecretStr

from app.domain.identity import (
    DeviceRole,
    IdentityClaimMismatchError,
)
from app.infrastructure.security.development_authenticator import (
    DevelopmentAuthenticationNotConfiguredError,
    DevelopmentDeviceAuthenticator,
    InvalidDeviceTokenError,
)
from app.settings import Settings


def test_game_token_resolves_server_owned_identity() -> None:
    settings = Settings(
        dev_game_device_token=SecretStr("game-secret"),
        dev_web_device_token=SecretStr("web-secret"),
    )

    identity = DevelopmentDeviceAuthenticator(settings).authenticate("game-secret")

    assert identity.profile_id == "profile-local-001"
    assert identity.device_id == "device-game-001"
    assert identity.role is DeviceRole.GAME_CLIENT
    identity.validate_claims(
        profile_id="profile-local-001",
        device_id="device-game-001",
    )


def test_mismatched_client_identity_claim_is_rejected() -> None:
    settings = Settings(
        dev_game_device_token=SecretStr("game-secret"),
        dev_web_device_token=SecretStr("web-secret"),
    )
    identity = DevelopmentDeviceAuthenticator(settings).authenticate("game-secret")

    with pytest.raises(IdentityClaimMismatchError):
        identity.validate_claims(
            profile_id="different-profile",
            device_id=None,
        )


def test_invalid_token_is_rejected() -> None:
    settings = Settings(
        dev_game_device_token=SecretStr("game-secret"),
        dev_web_device_token=SecretStr("web-secret"),
    )

    with pytest.raises(InvalidDeviceTokenError):
        DevelopmentDeviceAuthenticator(settings).authenticate("wrong-secret")


def test_empty_tokens_are_not_valid_configuration() -> None:
    settings = Settings(
        dev_game_device_token=SecretStr(""),
        dev_web_device_token=SecretStr(""),
    )

    with pytest.raises(DevelopmentAuthenticationNotConfiguredError):
        DevelopmentDeviceAuthenticator(settings).authenticate("anything")
