from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.application.errors import (
    DeviceAlreadyRegisteredError,
    DeviceNotFoundError,
    DeviceRoleNotAllowedError,
    DuplicateRequestError,
    ExpiredPairingCodeError,
    IdentityScopeMismatchError,
    InvalidPairingCodeError,
    UsedPairingCodeError,
)
from app.application.models.pairing import (
    CreatePairingCodeRequest,
    DeviceListResponse,
    DeviceRevocationResponse,
    DeviceSelfResponse,
    DeviceTokenResponse,
    DeviceView,
    PairDeviceRequest,
    PairingCodeResponse,
    RegisterGameRequest,
)
from app.application.ports.device_repository import (
    DeviceRecord,
    DeviceRepository,
    DeviceWriteConflictError,
    PairingCodeRecord,
)
from app.application.ports.credential_protector import CredentialProtection
from app.domain.identity import AuthenticatedDevice, DeviceRole


class PairingService:
    def __init__(
        self,
        repository: DeviceRepository,
        protector: CredentialProtection,
        pairing_code_ttl_seconds: int,
    ) -> None:
        self._repository = repository
        self._protector = protector
        self._pairing_code_ttl_seconds = pairing_code_ttl_seconds

    async def register_game(
        self, request: RegisterGameRequest
    ) -> DeviceTokenResponse:
        existing = await self._repository.find_device_by_creation_request(
            request.request_id
        )
        if existing is not None:
            if existing.role != DeviceRole.GAME_CLIENT.value:
                raise DuplicateRequestError
            return self._token_response(request.request_id, existing)
        if await self._repository.find_game_device() is not None:
            raise DeviceAlreadyRegisteredError

        now = datetime.now(timezone.utc)
        profile_id = await self._repository.find_profile_id()
        if profile_id is None:
            profile_id = f"profile-{uuid4()}"
            await self._repository.create_profile(profile_id, now)
            await self._repository.flush()
        device = await self._new_device(
            profile_id, DeviceRole.GAME_CLIENT, request.request_id, now
        )
        try:
            await self._repository.commit()
        except DeviceWriteConflictError:
            await self._repository.rollback()
            existing = await self._repository.find_device_by_creation_request(
                request.request_id
            )
            if existing is not None:
                if existing.role != DeviceRole.GAME_CLIENT.value:
                    raise DuplicateRequestError
                return self._token_response(request.request_id, existing)
            if await self._repository.find_game_device() is not None:
                raise DeviceAlreadyRegisteredError
            raise
        return self._token_response(request.request_id, device)

    async def create_pairing_code(
        self,
        request: CreatePairingCodeRequest,
        identity: AuthenticatedDevice,
    ) -> PairingCodeResponse:
        self._require_game(identity)
        existing = await self._repository.find_pairing_code_by_issue_request(
            identity.profile_id, request.request_id
        )
        if existing is not None:
            return self._pairing_code_response(request.request_id, existing)

        now = datetime.now(timezone.utc)
        pairing_code_id = f"pairing-{uuid4()}"
        code = self._protector.make_pairing_code(
            pairing_code_id, request.request_id
        )
        model = await self._repository.create_pairing_code(
            pairing_code_id=pairing_code_id,
            profile_id=identity.profile_id,
            issuing_device_id=identity.device_id,
            code_hash=self._protector.hash_value("pairing-code", code),
            issue_request_id=request.request_id,
            expires_at=now + timedelta(seconds=self._pairing_code_ttl_seconds),
            created_at=now,
        )
        try:
            await self._repository.commit()
        except DeviceWriteConflictError:
            await self._repository.rollback()
            existing = await self._repository.find_pairing_code_by_issue_request(
                identity.profile_id, request.request_id
            )
            if existing is None:
                raise
            return self._pairing_code_response(request.request_id, existing)
        return self._pairing_code_response(request.request_id, model)

    async def pair_device(self, request: PairDeviceRequest) -> DeviceTokenResponse:
        retried = await self._repository.find_pairing_code_by_redemption_request(
            request.request_id
        )
        if retried is not None:
            if not self._protector.verify(
                "pairing-code", request.pairing_code, retried.code_hash
            ):
                raise InvalidPairingCodeError
            if retried.paired_device_id is None:
                raise InvalidPairingCodeError
            device = await self._repository.get_device(retried.paired_device_id)
            if device is None:
                raise DeviceNotFoundError
            return self._token_response(request.request_id, device)

        pairing_code = await self._match_pairing_code(request.pairing_code)
        if pairing_code is None:
            raise InvalidPairingCodeError
        now = datetime.now(timezone.utc)
        if self._as_utc(pairing_code.expires_at) <= now:
            raise ExpiredPairingCodeError
        if pairing_code.used_at is not None:
            raise UsedPairingCodeError

        device = await self._new_device(
            pairing_code.profile_id,
            DeviceRole.WEB_CLIENT,
            request.request_id,
            now,
        )
        try:
            await self._repository.flush()
            pairing_code.used_at = now
            pairing_code.redeemed_request_id = request.request_id
            pairing_code.paired_device_id = device.device_id
            await self._repository.commit()
        except DeviceWriteConflictError:
            await self._repository.rollback()
            retried = await self._repository.find_pairing_code_by_redemption_request(
                request.request_id
            )
            if retried is None or retried.paired_device_id is None:
                raise DuplicateRequestError
            existing_device = await self._repository.get_device(
                retried.paired_device_id
            )
            if existing_device is None:
                raise DeviceNotFoundError
            return self._token_response(request.request_id, existing_device)
        return self._token_response(request.request_id, device)

    async def list_devices(
        self, request_id: str, identity: AuthenticatedDevice
    ) -> DeviceListResponse:
        self._require_game(identity)
        devices = await self._repository.list_devices(identity.profile_id)
        return DeviceListResponse(
            request_id=request_id,
            devices=[self._device_view(device) for device in devices],
        )

    async def get_current_device(
        self, request_id: str, identity: AuthenticatedDevice
    ) -> DeviceSelfResponse:
        self._require_web(identity)
        return DeviceSelfResponse(
            request_id=request_id,
            profile_id=identity.profile_id,
            device_id=identity.device_id,
        )

    async def revoke_current_device(
        self,
        request_id: str,
        identity: AuthenticatedDevice,
    ) -> DeviceRevocationResponse:
        self._require_web(identity)
        device = await self._repository.get_device(identity.device_id)
        if device is None:
            raise DeviceNotFoundError
        if device.profile_id != identity.profile_id:
            raise IdentityScopeMismatchError
        if device.revoked_at is None:
            device.revoked_at = datetime.now(timezone.utc)
            await self._repository.commit()
        return DeviceRevocationResponse(
            request_id=request_id,
            device_id=identity.device_id,
        )

    async def revoke_device(
        self,
        request_id: str,
        device_id: str,
        identity: AuthenticatedDevice,
    ) -> DeviceRevocationResponse:
        self._require_game(identity)
        device = await self._repository.get_device(device_id)
        if device is None:
            raise DeviceNotFoundError
        if device.profile_id != identity.profile_id:
            raise IdentityScopeMismatchError
        if device.role != DeviceRole.WEB_CLIENT.value:
            raise DeviceRoleNotAllowedError
        if device.revoked_at is None:
            device.revoked_at = datetime.now(timezone.utc)
            await self._repository.commit()
        return DeviceRevocationResponse(request_id=request_id, device_id=device_id)

    async def _match_pairing_code(self, raw_code: str) -> PairingCodeRecord | None:
        match = None
        for candidate in await self._repository.list_pairing_codes():
            if (
                self._protector.verify("pairing-code", raw_code, candidate.code_hash)
                and match is None
            ):
                match = candidate
        return match

    async def _new_device(
        self,
        profile_id: str,
        role: DeviceRole,
        request_id: str,
        now: datetime,
    ) -> DeviceRecord:
        device_id = f"device-{uuid4()}"
        lookup_id = f"token-{uuid4()}"
        token = self._protector.make_device_token(
            lookup_id=lookup_id,
            device_id=device_id,
            creation_request_id=request_id,
        )
        return await self._repository.create_device(
            device_id=device_id,
            profile_id=profile_id,
            role=role.value,
            token_lookup_id=lookup_id,
            token_hash=self._protector.hash_value("device-token", token),
            creation_request_id=request_id,
            created_at=now,
            game_registration_key=(
                "single-game-client" if role is DeviceRole.GAME_CLIENT else None
            ),
        )

    def _token_response(
        self, request_id: str, device: DeviceRecord
    ) -> DeviceTokenResponse:
        token = self._protector.make_device_token(
            lookup_id=device.token_lookup_id,
            device_id=device.device_id,
            creation_request_id=device.creation_request_id,
        )
        return DeviceTokenResponse(
            request_id=request_id,
            profile_id=device.profile_id,
            device=self._device_view(device),
            device_token=token,
        )

    def _pairing_code_response(
        self, request_id: str, model: PairingCodeRecord
    ) -> PairingCodeResponse:
        return PairingCodeResponse(
            request_id=request_id,
            pairing_code=self._protector.make_pairing_code(
                model.pairing_code_id, model.issue_request_id
            ),
            expires_at=self._as_utc(model.expires_at),
        )

    @staticmethod
    def _device_view(device: DeviceRecord) -> DeviceView:
        return DeviceView(
            device_id=device.device_id,
            role=DeviceRole(device.role),
            created_at=PairingService._as_utc(device.created_at),
            last_used_at=(
                PairingService._as_utc(device.last_used_at)
                if device.last_used_at is not None
                else None
            ),
            revoked_at=(
                PairingService._as_utc(device.revoked_at)
                if device.revoked_at is not None
                else None
            ),
        )

    @staticmethod
    def _require_game(identity: AuthenticatedDevice) -> None:
        if identity.role is not DeviceRole.GAME_CLIENT:
            raise DeviceRoleNotAllowedError

    @staticmethod
    def _require_web(identity: AuthenticatedDevice) -> None:
        if identity.role is not DeviceRole.WEB_CLIENT:
            raise DeviceRoleNotAllowedError

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
