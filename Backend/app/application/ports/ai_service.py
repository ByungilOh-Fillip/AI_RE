from typing import Protocol

from app.application.models.ai import AIServiceRequest, AIServiceResult


class AIService(Protocol):
    async def generate_chat(self, request: AIServiceRequest) -> AIServiceResult:
        """Return normalized, untrusted dialogue and candidate data."""
        ...
