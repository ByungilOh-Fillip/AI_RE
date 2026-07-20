from datetime import datetime
from typing import Literal

from pydantic import Field

from app.application.models.ai import StrictModel
from app.application.models.chat import StableId
from app.domain.identity import DeviceRole


class RegisterGameRequest(StrictModel):
    schema_version: Literal[1] = 1
    request_id: StableId


class CreatePairingCodeRequest(StrictModel):
    schema_version: Literal[1] = 1
    request_id: StableId


class PairDeviceRequest(StrictModel):
    schema_version: Literal[1] = 1
    request_id: StableId
    pairing_code: str = Field(pattern=r"^[0-9]{8}$")


class DeviceView(StrictModel):
    device_id: StableId
    role: DeviceRole
    created_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None


class DeviceTokenResponse(StrictModel):
    schema_version: Literal[1] = 1
    request_id: StableId
    profile_id: StableId
    device: DeviceView
    device_token: str = Field(min_length=32, max_length=512)


class PairingCodeResponse(StrictModel):
    schema_version: Literal[1] = 1
    request_id: StableId
    pairing_code: str = Field(pattern=r"^[0-9]{8}$")
    expires_at: datetime


class DeviceListResponse(StrictModel):
    schema_version: Literal[1] = 1
    request_id: StableId
    devices: list[DeviceView]


class DeviceRevocationResponse(StrictModel):
    schema_version: Literal[1] = 1
    request_id: StableId
    device_id: StableId
    status: Literal["Revoked"] = "Revoked"
