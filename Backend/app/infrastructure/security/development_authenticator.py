from secrets import compare_digest

from pydantic import SecretStr

from app.domain.identity import AuthenticatedDevice, DeviceRole
from app.settings import Settings


class DevelopmentAuthenticationNotConfiguredError(RuntimeError):
    pass


class InvalidDeviceTokenError(ValueError):
    pass


class DevelopmentDeviceAuthenticator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def authenticate(self, token: str) -> AuthenticatedDevice:
        game_token = self._read_secret(self._settings.dev_game_device_token)
        web_token = self._read_secret(self._settings.dev_web_device_token)
        if game_token is None or web_token is None:
            raise DevelopmentAuthenticationNotConfiguredError(
                "Development device tokens must be configured in the local environment."
            )

        if compare_digest(token, game_token):
            return AuthenticatedDevice(
                profile_id=self._settings.dev_profile_id,
                device_id=self._settings.dev_game_device_id,
                role=DeviceRole.GAME_CLIENT,
            )

        if compare_digest(token, web_token):
            return AuthenticatedDevice(
                profile_id=self._settings.dev_profile_id,
                device_id=self._settings.dev_web_device_id,
                role=DeviceRole.WEB_CLIENT,
            )

        raise InvalidDeviceTokenError("Device token is invalid.")

    @staticmethod
    def _read_secret(secret: SecretStr | None) -> str | None:
        if secret is None:
            return None

        value = secret.get_secret_value()
        return value if value else None
