from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.application.ports.device_repository import DeviceWriteConflictError
from app.infrastructure.database.models import DeviceModel, PairingCodeModel, ProfileModel


class SqlAlchemyDeviceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_profile_id(self) -> str | None:
        result = await self._session.execute(
            select(ProfileModel.profile_id).order_by(ProfileModel.created_at)
        )
        return result.scalars().first()

    async def find_device_by_creation_request(
        self, request_id: str
    ) -> DeviceModel | None:
        result = await self._session.execute(
            select(DeviceModel).where(DeviceModel.creation_request_id == request_id)
        )
        return result.scalar_one_or_none()

    async def find_game_device(self) -> DeviceModel | None:
        result = await self._session.execute(
            select(DeviceModel).where(DeviceModel.role == "GameClient")
        )
        return result.scalars().first()

    async def find_pairing_code_by_issue_request(
        self, profile_id: str, request_id: str
    ) -> PairingCodeModel | None:
        result = await self._session.execute(
            select(PairingCodeModel).where(
                PairingCodeModel.profile_id == profile_id,
                PairingCodeModel.issue_request_id == request_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_pairing_code_by_redemption_request(
        self, request_id: str
    ) -> PairingCodeModel | None:
        result = await self._session.execute(
            select(PairingCodeModel).where(
                PairingCodeModel.redeemed_request_id == request_id
            )
        )
        return result.scalar_one_or_none()

    async def list_pairing_codes(self) -> list[PairingCodeModel]:
        result = await self._session.execute(
            select(PairingCodeModel).order_by(PairingCodeModel.created_at.desc())
        )
        return list(result.scalars())

    async def list_devices(self, profile_id: str) -> list[DeviceModel]:
        result = await self._session.execute(
            select(DeviceModel)
            .where(DeviceModel.profile_id == profile_id)
            .order_by(DeviceModel.created_at)
        )
        return list(result.scalars())

    async def get_device(self, device_id: str) -> DeviceModel | None:
        return await self._session.get(DeviceModel, device_id)

    async def create_profile(self, profile_id: str, created_at: datetime) -> None:
        self._session.add(ProfileModel(profile_id=profile_id, created_at=created_at))

    async def create_device(self, **values: object) -> DeviceModel:
        device = DeviceModel(**values)
        self._session.add(device)
        return device

    async def create_pairing_code(self, **values: object) -> PairingCodeModel:
        pairing_code = PairingCodeModel(
            **values,
            used_at=None,
            redeemed_request_id=None,
            paired_device_id=None,
        )
        self._session.add(pairing_code)
        return pairing_code

    async def flush(self) -> None:
        try:
            await self._session.flush()
        except IntegrityError as error:
            raise DeviceWriteConflictError from error

    async def commit(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError as error:
            raise DeviceWriteConflictError from error

    async def rollback(self) -> None:
        await self._session.rollback()
