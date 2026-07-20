from dataclasses import dataclass
from enum import StrEnum


class DeviceRole(StrEnum):
    GAME_CLIENT = "GameClient"
    WEB_CLIENT = "WebClient"


class IdentityClaimMismatchError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AuthenticatedDevice:
    profile_id: str
    device_id: str
    role: DeviceRole

    def validate_claims(
        self,
        profile_id: str | None,
        device_id: str | None,
    ) -> None:
        if profile_id is not None and profile_id != self.profile_id:
            raise IdentityClaimMismatchError(
                "Client profile claim does not match authenticated identity."
            )

        if device_id is not None and device_id != self.device_id:
            raise IdentityClaimMismatchError(
                "Client device claim does not match authenticated identity."
            )
