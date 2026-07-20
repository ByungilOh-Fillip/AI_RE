from typing import Protocol


class CredentialProtection(Protocol):
    def make_device_token(
        self,
        *,
        lookup_id: str,
        device_id: str,
        creation_request_id: str,
    ) -> str: ...

    def make_pairing_code(self, pairing_code_id: str, issue_request_id: str) -> str: ...

    def hash_value(self, purpose: str, value: str) -> str: ...

    def verify(self, purpose: str, value: str, expected_hash: str) -> bool: ...
