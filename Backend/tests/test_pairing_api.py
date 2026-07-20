import asyncio
import io
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select

from app.infrastructure.database.base import Base
from app.infrastructure.database.connection import Database
from app.infrastructure.database.models import DeviceModel, PairingCodeModel, ProfileModel
from app.infrastructure.logging import JsonFormatter
from app.infrastructure.security.credentials import CredentialProtector
from app.main import create_app
from app.settings import Settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OFFLINE_FIXTURE = (
    PROJECT_ROOT / "Contracts" / "fixtures" / "chat" / "offline-request.valid.json"
)
BOOTSTRAP_TOKEN = "bootstrap-game-secret"
PEPPER = "persistent-test-pepper"


def make_settings(database_url: str, **overrides: object) -> Settings:
    return Settings(
        database_url=database_url,
        dev_game_device_token=SecretStr(BOOTSTRAP_TOKEN),
        device_credential_pepper=SecretStr(PEPPER),
        **overrides,
    )


async def create_schema(database_url: str) -> None:
    database = Database(database_url)
    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await database.dispose()


def register_game(client: TestClient, request_id: str = "register-game-001") -> dict:
    response = client.post(
        "/api/v1/devices/register-game",
        headers={"Authorization": f"Bearer {BOOTSTRAP_TOKEN}"},
        json={"schema_version": 1, "request_id": request_id},
    )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    return response.json()


def issue_pairing_code(client: TestClient, game_token: str) -> dict:
    response = client.post(
        "/api/v1/devices/pairing-codes",
        headers={"Authorization": f"Bearer {game_token}"},
        json={"schema_version": 1, "request_id": "pairing-code-001"},
    )
    assert response.status_code == 200
    return response.json()


def test_complete_pairing_chat_revocation_and_restart_flow(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'pairing.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    settings = make_settings(database_url)

    with TestClient(create_app(settings)) as client:
        game = register_game(client)
        duplicate = register_game(client)
        assert duplicate == game

        second_registration = client.post(
            "/api/v1/devices/register-game",
            headers={"Authorization": f"Bearer {BOOTSTRAP_TOKEN}"},
            json={"schema_version": 1, "request_id": "register-game-002"},
        )
        assert second_registration.status_code == 409
        assert second_registration.json()["error"]["code"] == "DeviceAlreadyRegistered"

        issued = issue_pairing_code(client, game["device_token"])
        paired = client.post(
            "/api/v1/devices/pair",
            json={
                "schema_version": 1,
                "request_id": "pair-web-001",
                "pairing_code": issued["pairing_code"],
            },
        )
        assert paired.status_code == 200
        web = paired.json()
        assert web["profile_id"] == game["profile_id"]
        assert web["device"]["role"] == "WebClient"

        paired_retry = client.post(
            "/api/v1/devices/pair",
            json={
                "schema_version": 1,
                "request_id": "pair-web-001",
                "pairing_code": issued["pairing_code"],
            },
        )
        assert paired_retry.json() == web

        reused = client.post(
            "/api/v1/devices/pair",
            json={
                "schema_version": 1,
                "request_id": "pair-web-002",
                "pairing_code": issued["pairing_code"],
            },
        )
        assert reused.status_code == 409
        assert reused.json()["error"]["code"] == "UsedPairingCode"

        devices = client.get(
            "/api/v1/devices",
            headers={
                "Authorization": f"Bearer {game['device_token']}",
                "X-Request-ID": "list-devices-001",
            },
        )
        assert devices.status_code == 200
        assert len(devices.json()["devices"]) == 2
        game_view = next(
            device
            for device in devices.json()["devices"]
            if device["role"] == "GameClient"
        )
        assert game_view["last_used_at"] is not None

        forbidden = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {web['device_token']}"},
        )
        assert forbidden.status_code == 403

        chat_body = json.loads(OFFLINE_FIXTURE.read_text(encoding="utf-8"))
        chat_body.pop("profile_id")
        chat_body.pop("device_id")
        chat = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {web['device_token']}"},
            json=chat_body,
        )
        assert chat.status_code == 200

        revoked = client.delete(
            f"/api/v1/devices/{web['device']['device_id']}",
            headers={"Authorization": f"Bearer {game['device_token']}"},
        )
        assert revoked.status_code == 200
        assert revoked.json()["status"] == "Revoked"

    with TestClient(create_app(settings)) as restarted_client:
        rejected = restarted_client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {web['device_token']}"},
            json=chat_body,
        )
        assert rejected.status_code == 401
        game_still_valid = restarted_client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {game['device_token']}"},
        )
        assert game_still_valid.status_code == 200

    async def assert_secrets_are_not_stored() -> None:
        database = Database(database_url)
        async with database.session_factory() as session:
            devices = list((await session.execute(select(DeviceModel))).scalars())
            codes = list((await session.execute(select(PairingCodeModel))).scalars())
        await database.dispose()
        assert all(device.token_hash != game["device_token"] for device in devices)
        assert all(device.token_hash != web["device_token"] for device in devices)
        assert all(code.code_hash != issued["pairing_code"] for code in codes)

    asyncio.run(assert_secrets_are_not_stored())


def test_invalid_expired_and_request_id_errors_use_envelopes(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'errors.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    settings = make_settings(database_url)
    with TestClient(create_app(settings)) as client:
        invalid = client.post(
            "/api/v1/devices/pair",
            json={
                "schema_version": 1,
                "request_id": "invalid-code-001",
                "pairing_code": "00000000",
            },
        )
        assert invalid.status_code == 400
        assert invalid.json()["error"]["code"] == "InvalidPairingCode"

        mismatch = client.post(
            "/api/v1/devices/register-game",
            headers={
                "Authorization": f"Bearer {BOOTSTRAP_TOKEN}",
                "X-Request-ID": "different-request-id",
            },
            json={"schema_version": 1, "request_id": "register-game-001"},
        )
        assert mismatch.status_code == 400
        assert mismatch.json()["error"]["code"] == "InvalidRequest"

        game = register_game(client)
        issued = issue_pairing_code(client, game["device_token"])

    async def expire_code() -> None:
        database = Database(database_url)
        async with database.session_factory() as session:
            code = (await session.execute(select(PairingCodeModel))).scalars().one()
            code.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            await session.commit()
        await database.dispose()

    asyncio.run(expire_code())
    with TestClient(create_app(settings)) as client:
        expired = client.post(
            "/api/v1/devices/pair",
            json={
                "schema_version": 1,
                "request_id": "expired-code-001",
                "pairing_code": issued["pairing_code"],
            },
        )
        assert expired.status_code == 410
        assert expired.json()["error"]["code"] == "ExpiredPairingCode"


def test_missing_security_configuration_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'config.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    monkeypatch.delenv("DEV_GAME_DEVICE_TOKEN", raising=False)
    monkeypatch.delenv("DEVICE_CREDENTIAL_PEPPER", raising=False)
    app = create_app(Settings(database_url=database_url, _env_file=None))

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/devices/register-game",
            headers={"Authorization": "Bearer any-token"},
            json={"schema_version": 1, "request_id": "register-game-001"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AuthenticationUnavailable"


def test_registration_reuses_existing_single_profile(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'existing.db').as_posix()}"
    asyncio.run(create_schema(database_url))

    async def seed_profile() -> None:
        database = Database(database_url)
        async with database.session_factory() as session:
            session.add(
                ProfileModel(
                    profile_id="existing-profile",
                    created_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()
        await database.dispose()

    asyncio.run(seed_profile())
    with TestClient(create_app(make_settings(database_url))) as client:
        registered = register_game(client)

    assert registered["profile_id"] == "existing-profile"


def test_other_profile_device_cannot_be_revoked_and_secrets_are_not_logged(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'scope.db').as_posix()}"
    asyncio.run(create_schema(database_url))
    settings = make_settings(database_url)
    with TestClient(create_app(settings)) as client:
        game = register_game(client)
        issued = issue_pairing_code(client, game["device_token"])

    async def seed_other_profile() -> None:
        database = Database(database_url)
        now = datetime.now(timezone.utc)
        protector = CredentialProtector(SecretStr(PEPPER))
        token = protector.make_device_token(
            lookup_id="other-token",
            device_id="other-web-device",
            creation_request_id="other-device-request",
        )
        async with database.session_factory() as session:
            session.add(ProfileModel(profile_id="other-profile", created_at=now))
            await session.flush()
            session.add(
                DeviceModel(
                    device_id="other-web-device",
                    profile_id="other-profile",
                    role="WebClient",
                    token_lookup_id="other-token",
                    token_hash=protector.hash_value("device-token", token),
                    creation_request_id="other-device-request",
                    game_registration_key=None,
                    created_at=now,
                    last_used_at=None,
                    revoked_at=None,
                )
            )
            await session.commit()
        await database.dispose()

    asyncio.run(seed_other_profile())
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("aire.backend")
    logger.addHandler(handler)
    try:
        with TestClient(create_app(settings)) as client:
            paired = client.post(
                "/api/v1/devices/pair",
                json={
                    "schema_version": 1,
                    "request_id": "logged-pairing-request",
                    "pairing_code": issued["pairing_code"],
                },
            )
            assert paired.status_code == 200
            response = client.delete(
                "/api/v1/devices/other-web-device",
                headers={"Authorization": f"Bearer {game['device_token']}"},
            )
    finally:
        logger.removeHandler(handler)

    assert response.status_code == 403
    output = stream.getvalue()
    assert game["device_token"] not in output
    assert issued["pairing_code"] not in output
