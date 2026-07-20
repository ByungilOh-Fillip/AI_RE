import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.application.models.ai import (
    AIServiceRequest,
    AIServiceResult,
    CommandType,
    InteractionMode,
    RealWorldTimeContext,
)
from app.infrastructure.ai.mock import MockAIService

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AI_FIXTURES = PROJECT_ROOT / "Contracts" / "fixtures" / "ai-service"


def test_mock_ai_service_returns_normalized_offline_result() -> None:
    request = AIServiceRequest(
        request_id="request-offline-001",
        current_message_id="message-user-001",
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


def test_mock_ai_service_returns_allowed_command_candidate() -> None:
    request = AIServiceRequest(
        request_id="request-ingame-command-001",
        current_message_id="message-user-command-001",
        interaction_mode=InteractionMode.IN_GAME,
        companion_id="companion-01",
        user_message="여기서 기다려 줘.",
        time_context={
            "source": "GameWorld",
            "day": 18,
            "hour": 14.5,
            "period": "Afternoon",
        },
        allowed_commands=[CommandType.HOLD_POSITION],
    )

    result = asyncio.run(MockAIService("command").generate_chat(request))

    assert [candidate.type for candidate in result.command_candidates] == [
        CommandType.HOLD_POSITION
    ]
    assert result.memory_candidates == []


def test_mock_ai_service_returns_current_message_memory_candidate() -> None:
    request = AIServiceRequest(
        request_id="request-offline-memory-001",
        current_message_id="message-user-memory-001",
        interaction_mode=InteractionMode.OFFLINE,
        companion_id="companion-01",
        user_message="오늘 중요한 일정이 있어.",
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

    result = asyncio.run(MockAIService("memory").generate_chat(request))

    assert result.memory_candidates[0].source_ids == [request.current_message_id]
    assert result.memory_candidates[0].source_mode is InteractionMode.OFFLINE


@pytest.mark.parametrize(
    ("scenario", "request_fixture", "result_fixture"),
    [
        ("normal", "request.valid.json", "result.valid.json"),
        ("command", "request.command.valid.json", "result.command.valid.json"),
        ("memory", "request.memory.valid.json", "result.memory.valid.json"),
    ],
)
def test_mock_scenarios_match_shared_fixtures(
    scenario: str,
    request_fixture: str,
    result_fixture: str,
) -> None:
    request = AIServiceRequest.model_validate_json(
        (AI_FIXTURES / request_fixture).read_text(encoding="utf-8")
    )
    expected = AIServiceResult.model_validate_json(
        (AI_FIXTURES / result_fixture).read_text(encoding="utf-8")
    )

    result = asyncio.run(MockAIService(scenario).generate_chat(request))

    assert result == expected
