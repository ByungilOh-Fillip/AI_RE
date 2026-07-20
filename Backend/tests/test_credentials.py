from pydantic import SecretStr

from app.infrastructure.security.credentials import CredentialProtector


def test_device_token_is_deterministic_and_hash_verifies() -> None:
    protector = CredentialProtector(SecretStr("unit-test-pepper"))
    token = protector.make_device_token(
        lookup_id="lookup-001",
        device_id="device-001",
        creation_request_id="request-001",
    )

    assert token.startswith("lookup-001.")
    assert token == protector.make_device_token(
        lookup_id="lookup-001",
        device_id="device-001",
        creation_request_id="request-001",
    )
    token_hash = protector.hash_value("device-token", token)
    assert protector.verify("device-token", token, token_hash)
    assert not protector.verify("device-token", f"{token}x", token_hash)


def test_pairing_code_is_eight_numeric_digits() -> None:
    protector = CredentialProtector(SecretStr("unit-test-pepper"))

    code = protector.make_pairing_code("pairing-001", "request-001")

    assert len(code) == 8
    assert code.isdigit()
