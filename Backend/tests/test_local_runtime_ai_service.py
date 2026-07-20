import asyncio
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from pydantic import ValidationError

from app.application.errors import (
    AIServiceInvalidOutputError,
    AIServiceTimeoutError,
    AIServiceUnavailableError,
)
from app.application.models.ai import (
    AIServiceRequest,
    InteractionMode,
    RealWorldTimeContext,
)
from app.infrastructure.ai.local_runtime import (
    HttpLocalRuntimeTransport,
    LocalRuntimeAIService,
)
from app.settings import Settings


def make_request() -> AIServiceRequest:
    return AIServiceRequest(
        request_id="request-local-001",
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


def make_result() -> dict[str, object]:
    return {
        "schema_version": 1,
        "request_id": "request-local-001",
        "display_text": "정상 Local Runtime 응답",
        "command_candidates": [],
        "memory_candidates": [],
        "metadata": {
            "provider": "fake-runtime",
            "model_version": "fake-model-v1",
            "prompt_version": "prompt-v1",
        },
    }


def make_service(handler: httpx.MockTransport) -> LocalRuntimeAIService:
    transport = HttpLocalRuntimeTransport(
        base_url="http://runtime.test",
        timeout_seconds=1.0,
        http_transport=handler,
    )
    return LocalRuntimeAIService(
        model_name="fake-model",
        prompt_version="prompt-v1",
        transport=transport,
    )


def test_local_runtime_adapter_validates_normalized_result() -> None:
    captured_payload: dict[str, object] = {}

    def handle(request: httpx.Request) -> httpx.Response:
        captured_payload.update(json.loads(request.content))
        return httpx.Response(200, json=make_result())

    result = asyncio.run(
        make_service(httpx.MockTransport(handle)).generate_chat(make_request())
    )

    assert result.display_text == "정상 Local Runtime 응답"
    assert captured_payload["model"] == "fake-model"
    assert captured_payload["prompt_version"] == "prompt-v1"
    assert captured_payload["input"]["current_message_id"] == "message-user-001"
    assert "profile_id" not in captured_payload["input"]
    assert "device_id" not in captured_payload["input"]


@pytest.mark.parametrize(
    ("response", "expected_error"),
    [
        (httpx.Response(200, content=b"not-json"), AIServiceInvalidOutputError),
        (
            httpx.Response(200, json={"schema_version": 99}),
            AIServiceInvalidOutputError,
        ),
        (httpx.Response(503), AIServiceUnavailableError),
        (httpx.Response(504), AIServiceTimeoutError),
    ],
)
def test_local_runtime_adapter_normalizes_response_failures(
    response: httpx.Response,
    expected_error: type[Exception],
) -> None:
    service = make_service(httpx.MockTransport(lambda _request: response))

    with pytest.raises(expected_error):
        asyncio.run(service.generate_chat(make_request()))


@pytest.mark.parametrize(
    ("transport_error", "expected_error"),
    [
        (httpx.ConnectError("unavailable"), AIServiceUnavailableError),
        (httpx.ReadTimeout("timeout"), AIServiceTimeoutError),
    ],
)
def test_local_runtime_adapter_normalizes_transport_failures(
    transport_error: Exception,
    expected_error: type[Exception],
) -> None:
    def handle(_request: httpx.Request) -> httpx.Response:
        raise transport_error

    service = make_service(httpx.MockTransport(handle))

    with pytest.raises(expected_error):
        asyncio.run(service.generate_chat(make_request()))


def test_mock_settings_do_not_require_runtime_configuration() -> None:
    settings = Settings(ai_mode="mock")

    assert settings.ai_runtime_base_url is None
    assert settings.ai_model_name is None


def test_local_settings_require_runtime_model_and_prompt() -> None:
    with pytest.raises(ValidationError, match="AI_RUNTIME_BASE_URL"):
        Settings(ai_mode="local")
