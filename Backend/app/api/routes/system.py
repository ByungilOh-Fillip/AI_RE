from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.settings import Settings, get_settings

router = APIRouter(tags=["System"])


class HealthResponse(BaseModel):
    service: Literal["aire-backend"] = "aire-backend"
    status: Literal["ok"] = "ok"
    schema_version: int
    ai_mode: Literal["mock", "local"]


class CapabilitiesResponse(BaseModel):
    schema_version: int
    ai_mode: Literal["mock", "local"]
    capabilities: list[str]


@router.get("/health", response_model=HealthResponse)
def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        schema_version=settings.schema_version,
        ai_mode=settings.ai_mode,
    )


@router.get(
    "/api/v1/system/capabilities",
    response_model=CapabilitiesResponse,
)
def get_capabilities(
    settings: Settings = Depends(get_settings),
) -> CapabilitiesResponse:
    return CapabilitiesResponse(
        schema_version=settings.schema_version,
        ai_mode=settings.ai_mode,
        capabilities=["Health", "MockFoundation"],
    )
