import base64
import hashlib
import hmac
from secrets import compare_digest

from pydantic import SecretStr


class CredentialProtectionNotConfiguredError(RuntimeError):
    pass


class CredentialProtector:
    def __init__(self, pepper: SecretStr | None) -> None:
        if pepper is None or not pepper.get_secret_value():
            raise CredentialProtectionNotConfiguredError(
                "Device credential protection is not configured."
            )
        self._key = pepper.get_secret_value().encode("utf-8")

    def make_device_token(
        self,
        *,
        lookup_id: str,
        device_id: str,
        creation_request_id: str,
    ) -> str:
        secret = self._digest(
            f"device-secret:{device_id}:{creation_request_id}"
        )
        encoded = base64.urlsafe_b64encode(secret).decode("ascii").rstrip("=")
        return f"{lookup_id}.{encoded}"

    def make_pairing_code(self, pairing_code_id: str, issue_request_id: str) -> str:
        digest = self._digest(
            f"pairing-code:{pairing_code_id}:{issue_request_id}"
        )
        return f"{int.from_bytes(digest[:8], 'big') % 100_000_000:08d}"

    def hash_value(self, purpose: str, value: str) -> str:
        return self._digest(f"{purpose}:{value}").hex()

    def verify(self, purpose: str, value: str, expected_hash: str) -> bool:
        return compare_digest(self.hash_value(purpose, value), expected_hash)

    def _digest(self, value: str) -> bytes:
        return hmac.new(self._key, value.encode("utf-8"), hashlib.sha256).digest()
