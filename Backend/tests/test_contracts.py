import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_ROOT = PROJECT_ROOT / "Contracts"
SCHEMAS_ROOT = CONTRACTS_ROOT / "schemas"
FIXTURES_ROOT = CONTRACTS_ROOT / "fixtures"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_registry() -> Registry:
    registry = Registry()
    for path in SCHEMAS_ROOT.glob("*.schema.json"):
        schema = load_json(path)
        registry = registry.with_resource(
            schema["$id"],
            Resource.from_contents(schema),
        )
    return registry


@pytest.mark.parametrize(
    ("fixture_path", "schema_name"),
    [
        ("chat/offline-request.valid.json", "chat-request.schema.json"),
        ("chat/ingame-request.valid.json", "chat-request.schema.json"),
        ("chat/response.valid.json", "chat-response.schema.json"),
        ("commands/follow.valid.json", "command.schema.json"),
        ("events/combat-started.valid.json", "event.schema.json"),
        ("memory/user-shared-event.valid.json", "memory-candidate.schema.json"),
        ("errors/ai-service-unavailable.valid.json", "error-envelope.schema.json"),
        ("errors/request-too-large.valid.json", "error-envelope.schema.json"),
        ("errors/duplicate-request.valid.json", "error-envelope.schema.json"),
        ("ai-service/request.valid.json", "ai-service-request.schema.json"),
        ("ai-service/result.valid.json", "ai-service-result.schema.json"),
        ("ai-service/request.command.valid.json", "ai-service-request.schema.json"),
        ("ai-service/result.command.valid.json", "ai-service-result.schema.json"),
        ("ai-service/request.memory.valid.json", "ai-service-request.schema.json"),
        ("ai-service/result.memory.valid.json", "ai-service-result.schema.json"),
        ("devices/register-game.valid.json", "register-game-request.schema.json"),
        ("devices/pair.valid.json", "pair-device-request.schema.json"),
    ],
)
def test_valid_fixture_matches_schema(fixture_path: str, schema_name: str) -> None:
    validator = Draft202012Validator(
        load_json(SCHEMAS_ROOT / schema_name),
        registry=build_registry(),
        format_checker=FormatChecker(),
    )

    validator.validate(load_json(FIXTURES_ROOT / fixture_path))


def test_missing_time_context_fixture_is_rejected() -> None:
    validator = Draft202012Validator(
        load_json(SCHEMAS_ROOT / "chat-request.schema.json"),
        registry=build_registry(),
        format_checker=FormatChecker(),
    )

    with pytest.raises(ValidationError):
        validator.validate(
            load_json(
                FIXTURES_ROOT / "chat/request.invalid-missing-time-context.json"
            )
        )


def test_ai_service_fixtures_exclude_sensitive_identity_and_credentials() -> None:
    forbidden_keys = {
        "authorization",
        "connectionstring",
        "databaseconnectionstring",
        "databaseurl",
        "deviceid",
        "pairingcode",
        "password",
        "profileid",
        "secret",
        "token",
    }

    def assert_safe(value: Any) -> None:
        if isinstance(value, dict):
            for key, nested_value in value.items():
                normalized_key = "".join(
                    character
                    for character in key.casefold()
                    if character.isalnum()
                )
                assert normalized_key not in forbidden_keys
                assert not normalized_key.endswith(("password", "secret", "token"))
                assert_safe(nested_value)
        elif isinstance(value, list):
            for nested_value in value:
                assert_safe(nested_value)

    for fixture_path in (FIXTURES_ROOT / "ai-service").glob("*.json"):
        assert_safe(load_json(fixture_path))


def test_openapi_document_and_external_refs_exist() -> None:
    openapi_path = CONTRACTS_ROOT / "openapi.yaml"
    document = yaml.safe_load(openapi_path.read_text(encoding="utf-8"))

    assert document["openapi"] == "3.1.0"
    assert "/health" in document["paths"]
    assert "/api/v1/chat" in document["paths"]
    assert "/api/v1/devices/register-game" in document["paths"]
    assert "/api/v1/devices/pairing-codes" in document["paths"]
    assert "/api/v1/devices/pair" in document["paths"]
    assert "/api/v1/devices/me" in document["paths"]

    def collect_external_refs(value: Any) -> list[str]:
        if isinstance(value, dict):
            refs = []
            for key, nested_value in value.items():
                if key == "$ref" and isinstance(nested_value, str):
                    if nested_value.startswith("./"):
                        refs.append(nested_value)
                refs.extend(collect_external_refs(nested_value))
            return refs

        if isinstance(value, list):
            refs = []
            for nested_value in value:
                refs.extend(collect_external_refs(nested_value))
            return refs

        return []

    for reference in collect_external_refs(document):
        relative_path = reference.split("#", maxsplit=1)[0]
        assert (CONTRACTS_ROOT / relative_path).is_file()


@pytest.mark.parametrize(
    ("fixture_name", "definition_name"),
    [
        ("me.valid.json", "deviceSelfResponse"),
        ("revoke-me.valid.json", "deviceRevocationResponse"),
    ],
)
def test_device_response_fixture_matches_schema(
    fixture_name: str,
    definition_name: str,
) -> None:
    schema = load_json(SCHEMAS_ROOT / "device-pairing.schema.json")
    validator = Draft202012Validator(
        {"$ref": f"{schema['$id']}#/$defs/{definition_name}"},
        registry=build_registry(),
        format_checker=FormatChecker(),
    )

    validator.validate(load_json(FIXTURES_ROOT / "devices" / fixture_name))
