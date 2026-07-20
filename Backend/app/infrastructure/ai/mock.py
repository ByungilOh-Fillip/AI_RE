from app.application.models.ai import (
    AIMetadata,
    AIServiceRequest,
    AIServiceResult,
    InteractionMode,
)


class MockAIService:
    async def generate_chat(self, request: AIServiceRequest) -> AIServiceResult:
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
