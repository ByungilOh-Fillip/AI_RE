from typing import Annotated

from fastapi import Depends

from app.application.ports.ai_service import AIService
from app.infrastructure.ai.local_runtime import (
    HttpLocalRuntimeTransport,
    LocalRuntimeAIService,
)
from app.infrastructure.ai.mock import MockAIService
from app.settings import Settings, get_settings


def get_ai_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AIService:
    if settings.ai_mode == "mock":
        return MockAIService(settings.mock_ai_scenario)

    assert settings.ai_runtime_base_url is not None
    assert settings.ai_model_name is not None
    assert settings.ai_prompt_version is not None
    transport = HttpLocalRuntimeTransport(
        base_url=settings.ai_runtime_base_url,
        timeout_seconds=settings.ai_request_timeout_seconds,
    )
    return LocalRuntimeAIService(
        model_name=settings.ai_model_name,
        prompt_version=settings.ai_prompt_version,
        transport=transport,
    )
