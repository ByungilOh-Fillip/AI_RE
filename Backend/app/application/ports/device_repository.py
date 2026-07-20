from datetime import datetime
from typing import Protocol


class DeviceRecord(Protocol):
    device_id: str
    profile_id: str
    role: str
    token_lookup_id: str
    token_hash: str
    creation_request_id: str
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class PairingCodeRecord(Protocol):
    pairing_code_id: str
    profile_id: str
    issuing_device_id: str
    code_hash: str
    issue_request_id: str
    expires_at: datetime
    used_at: datetime | None
    created_at: datetime
    redeemed_request_id: str | None
    paired_device_id: str | None


class DeviceWriteConflictError(RuntimeError):
    pass


class DeviceRepository(Protocol):
    async def find_profile_id(self) -> str | None: ...

    async def find_device_by_creation_request(
        self, request_id: str
    ) -> DeviceRecord | None: ...

    async def find_game_device(self) -> DeviceRecord | None: ...

    async def find_pairing_code_by_issue_request(
        self, profile_id: str, request_id: str
    ) -> PairingCodeRecord | None: ...

    async def find_pairing_code_by_redemption_request(
        self, request_id: str
    ) -> PairingCodeRecord | None: ...

    async def list_pairing_codes(self) -> list[PairingCodeRecord]: ...

    async def list_devices(self, profile_id: str) -> list[DeviceRecord]: ...

    async def get_device(self, device_id: str) -> DeviceRecord | None: ...

    async def create_profile(self, profile_id: str, created_at: datetime) -> None: ...

    async def create_device(
        self,
        *,
        device_id: str,
        profile_id: str,
        role: str,
        token_lookup_id: str,
        token_hash: str,
        creation_request_id: str,
        created_at: datetime,
        game_registration_key: str | None,
    ) -> DeviceRecord: ...

    async def create_pairing_code(
        self,
        *,
        pairing_code_id: str,
        profile_id: str,
        issuing_device_id: str,
        code_hash: str,
        issue_request_id: str,
        expires_at: datetime,
        created_at: datetime,
    ) -> PairingCodeRecord: ...

    async def flush(self) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
