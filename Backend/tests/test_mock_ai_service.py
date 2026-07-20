import asyncio
from datetime import datetime, timedelta, timezone

from app.application.models.ai import (
    AIServiceRequest,
    InteractionMode,
    RealWorldTimeContext,
)
from app.infrastructure.ai.mock import MockAIService


def test_mock_ai_service_returns_normalized_offline_result() -> None:
    request = AIServiceRequest(
        request_id="request-offline-001",
        interaction_mode=InteractionMode.OFFLINE,
        companion_id="companion-01",
        user_message="테스트 메시지",
        time_context=RealWorldTimeContext(
            observed_at=datetime(
                2026,
                7,
                15,
                13,
                tzinfo=timezone(timedelta(hours=9)),
            ),
            timezone="Asia/Seoul",
        ),
    )

    result = asyncio.run(MockAIService().generate_chat(request))

    assert result.request_id == request.request_id
    assert result.metadata.provider == "mock"
    assert result.command_candidates == []
