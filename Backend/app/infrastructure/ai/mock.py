import asyncio
from datetime import datetime, timedelta, timezone

from app.application.errors import (
    AIServiceInvalidOutputError,
    AIServiceUnavailableError,
)
from app.application.models.ai import (
    AIMetadata,
    AIServiceRequest,
    AIServiceResult,
    CommandCandidate,
    InteractionMode,
    MemoryCandidate,
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
        issued_at = datetime(2026, 7, 15, 5, 30, tzinfo=timezone.utc)
        command_candidates = []
        if self._scenario == "command" and request.allowed_commands:
            command_candidates = [
                CommandCandidate(
                    command_id="command-mock-001",
                    request_id=request.request_id,
                    type=request.allowed_commands[0],
                    issued_at=issued_at,
                    expires_at=issued_at + timedelta(seconds=5),
                )
            ]

        memory_candidates = []
        if self._scenario == "memory":
            occurred_at = (
                request.time_context.observed_at
                if request.time_context.source == "RealWorld"
                else issued_at
            )
            memory_candidates = [
                MemoryCandidate(
                    candidate_id="memory-candidate-001",
                    type="UserSharedEvent",
                    summary="사용자가 현재 대화에서 직접 공유한 내용을 기억 후보로 만들었어.",
                    source_ids=[request.current_message_id],
                    source_mode=request.interaction_mode,
                    occurred_at=occurred_at,
                    confidence=1.0,
                )
            ]

        return AIServiceResult(
            request_id=request.request_id,
            display_text=display_text,
            command_candidates=command_candidates,
            memory_candidates=memory_candidates,
            metadata=AIMetadata(
                provider="mock",
                model_version="mock-v1",
                prompt_version="mock-v1",
            ),
        )
