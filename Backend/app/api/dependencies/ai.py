from typing import Annotated

from fastapi import Depends

from app.application.errors import AIServiceUnavailableError
from app.application.models.ai import AIServiceRequest, AIServiceResult
from app.application.ports.ai_service import AIService
from app.infrastructure.ai.mock import MockAIService
from app.settings import Settings, get_settings


class UnavailableLocalAIService:
    async def generate_chat(self, request: AIServiceRequest) -> AIServiceResult:
        del request
        raise AIServiceUnavailableError


def get_ai_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AIService:
    if settings.ai_mode == "mock":
        return MockAIService(settings.mock_ai_scenario)
    return UnavailableLocalAIService()
