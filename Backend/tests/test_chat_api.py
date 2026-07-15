import asyncio
import io
import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.infrastructure.database.base import Base
from app.infrastructure.database.connection import Database
from app.infrastructure.database.models import ChatRequestModel, MessageModel
from app.infrastructure.logging import JsonFormatter
from app.main import create_app
from app.settings import Settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OFFLINE_FIXTURE = (
    PROJECT_ROOT / "Contracts" / "fixtures" / "chat" / "offline-request.valid.json"
)
INGAME_FIXTURE = (
    PROJECT_ROOT / "Contracts" / "fixtures" / "chat" / "ingame-request.valid.json"
)


def make_settings(database_url: str, **overrides: object) -> Settings:
    return Settings(
        database_url=database_url,
        dev_game_device_token="game-secret",
        dev_web_device_token="web-secret",
        **overrides,
    )


async def create_schema(database_url: str) -> None:
    database = Database(database_url)
    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await database.dispose()


def load_offline_request() -> dict[str, object]:
    return json.loads(OFFLINE_FIXTURE.read_text(encoding="utf-8"))


def test_offline_chat_is_authenticated_persisted_and_idempotent(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'chat.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    app = create_app(make_settings(database_url))
    request_body = load_offline_request()
    headers = {
        "Authorization": "Bearer web-secret",
        "X-Request-ID": str(request_body["request_id"]),
    }

    with TestClient(app) as client:
        first = client.post("/api/v1/chat", headers=headers, json=request_body)

    restarted_app = create_app(make_settings(database_url))
    with TestClient(restarted_app) as client:
        duplicate = client.post("/api/v1/chat", headers=headers, json=request_body)

    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert duplicate.json() == first.json()
    assert first.headers["X-Request-ID"] == request_body["request_id"]
    assert first.json()["display_text"] == "현실 시간 기준의 Mock 응답이야."

    async def count_messages() -> int:
        database = Database(database_url)
        async with database.session_factory() as session:
            result = await session.scalar(select(func.count()).select_from(MessageModel))
        await database.dispose()
        return int(result or 0)

    assert asyncio.run(count_messages()) == 2


def test_ingame_chat_requires_game_role_and_game_world_time(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'ingame.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    app = create_app(make_settings(database_url))
    request_body = json.loads(INGAME_FIXTURE.read_text(encoding="utf-8"))
    wrong_role_body = dict(request_body)
    wrong_role_body.pop("profile_id")
    wrong_role_body.pop("device_id")
    wrong_role_body["request_id"] = "request-ingame-wrong-role"

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            headers={
                "Authorization": "Bearer game-secret",
                "X-Request-ID": str(request_body["request_id"]),
            },
            json=request_body,
        )
        wrong_role = client.post(
            "/api/v1/chat",
            headers={
                "Authorization": "Bearer web-secret",
                "X-Request-ID": str(wrong_role_body["request_id"]),
            },
            json=wrong_role_body,
        )

    assert response.status_code == 200
    assert response.json()["display_text"] == "게임 시간 기준의 Mock 응답이야."
    assert wrong_role.status_code == 403
    assert wrong_role.json()["error"]["code"] == "UnauthorizedDevice"


def test_reused_request_id_with_different_content_is_rejected(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'duplicate.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    app = create_app(make_settings(database_url))
    request_body = load_offline_request()
    headers = {
        "Authorization": "Bearer web-secret",
        "X-Request-ID": str(request_body["request_id"]),
    }

    with TestClient(app) as client:
        assert client.post("/api/v1/chat", headers=headers, json=request_body).status_code == 200
        request_body["user_message"] = "다른 내용"
        conflict = client.post("/api/v1/chat", headers=headers, json=request_body)

    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "DuplicateRequest"


def test_failed_message_transaction_leaves_no_partial_rows(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'rollback.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    app = create_app(make_settings(database_url))
    first_body = load_offline_request()
    second_body = load_offline_request()
    second_body["request_id"] = "request-offline-rollback"
    headers = {"Authorization": "Bearer web-secret"}

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/chat",
            headers={**headers, "X-Request-ID": str(first_body["request_id"])},
            json=first_body,
        )
        conflict = client.post(
            "/api/v1/chat",
            headers={**headers, "X-Request-ID": str(second_body["request_id"])},
            json=second_body,
        )

    assert first.status_code == 200
    assert conflict.status_code == 409

    async def count_rows() -> tuple[int, int]:
        database = Database(database_url)
        async with database.session_factory() as session:
            messages = await session.scalar(select(func.count()).select_from(MessageModel))
            requests = await session.scalar(
                select(func.count()).select_from(ChatRequestModel)
            )
        await database.dispose()
        return int(messages or 0), int(requests or 0)

    assert asyncio.run(count_rows()) == (2, 1)


def test_body_request_id_is_adopted_when_header_is_absent(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'adopt-id.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    app = create_app(make_settings(database_url))
    request_body = load_offline_request()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": "Bearer web-secret"},
            json=request_body,
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_body["request_id"]


def test_request_logs_exclude_token_and_conversation_text(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'logging.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    app = create_app(make_settings(database_url))
    request_body = load_offline_request()
    private_text = "민감한 현실 대화 원문"
    request_body["user_message"] = private_text
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("aire.backend")
    logger.addHandler(handler)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/chat",
                headers={
                    "Authorization": "Bearer web-secret",
                    "X-Request-ID": str(request_body["request_id"]),
                },
                json=request_body,
            )
    finally:
        logger.removeHandler(handler)

    assert response.status_code == 200
    log_output = stream.getvalue()
    assert "web-secret" not in log_output
    assert private_text not in log_output
    assert '"event":"request_complete"' in log_output


@pytest.mark.parametrize(
    ("scenario", "status_code", "error_code"),
    [
        ("unavailable", 503, "AIServiceUnavailable"),
        ("invalid_output", 503, "AIServiceInvalidOutput"),
        ("timeout", 504, "AIServiceTimeout"),
    ],
)
def test_mock_ai_failures_use_standard_error_envelope(
    tmp_path: Path,
    scenario: str,
    status_code: int,
    error_code: str,
) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / f'{scenario}.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    app = create_app(
        make_settings(
            database_url,
            mock_ai_scenario=scenario,
            ai_request_timeout_seconds=0.01,
        )
    )
    request_body = load_offline_request()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            headers={
                "Authorization": "Bearer web-secret",
                "X-Request-ID": str(request_body["request_id"]),
            },
            json=request_body,
        )

    assert response.status_code == status_code
    assert response.json()["error"]["code"] == error_code
    assert response.json()["request_id"] == request_body["request_id"]


def test_chat_rejects_missing_authentication_with_standard_error(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'auth.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    app = create_app(make_settings(database_url))
    request_body = load_offline_request()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            headers={"X-Request-ID": str(request_body["request_id"])},
            json=request_body,
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UnauthorizedDevice"


def test_chat_rejects_mismatched_time_context(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'time.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    app = create_app(make_settings(database_url))
    request_body = load_offline_request()
    request_body["time_context"] = {
        "source": "GameWorld",
        "day": 1,
        "hour": 12,
        "period": "Afternoon",
    }

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            headers={
                "Authorization": "Bearer web-secret",
                "X-Request-ID": str(request_body["request_id"]),
            },
            json=request_body,
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "InvalidRequest"
