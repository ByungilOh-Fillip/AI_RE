from app.application.models.ai import (
    AIMetadata,
    AIServiceRequest,
    AIServiceResult,
    InteractionMode,
)


class MockAIService:
    def __init__(self, scenario: str = "normal") -> None:
        self._scenario = scenario

    async def generate_chat(self, request: AIServiceRequest) -> AIServiceResult:
        if self._scenario == "timeout":
            await asyncio.sleep(3600)
        if self._scenario == "unavailable":
            raise AIServiceUnavailableError
        if self._scenario == "invalid_output":
            raise AIServiceInvalidOutputError

        display_text = (
            "현실 시간 기준의 Mock 응답이야."
            if request.interaction_mode is InteractionMode.OFFLINE
            else "게임 시간 기준의 Mock 응답이야."
        )
        return AIServiceResult(
            request_id=request.request_id,
            display_text=display_text,
            metadata=AIMetadata(
                provider="mock",
                model_version="mock-v1",
                prompt_version="mock-v1",
            ),
        )
import asyncio

from app.application.errors import (
    AIServiceInvalidOutputError,
    AIServiceUnavailableError,
)
