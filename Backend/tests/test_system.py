from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_uses_mock_mode_by_default() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "aire-backend",
        "status": "ok",
        "schema_version": 1,
        "ai_mode": "mock",
    }


def test_capabilities_report_foundation() -> None:
    response = client.get("/api/v1/system/capabilities")

    assert response.status_code == 200
    assert response.json()["capabilities"] == ["Health", "MockFoundation"]
