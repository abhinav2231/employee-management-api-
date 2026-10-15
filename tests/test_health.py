from fastapi.testclient import TestClient


def test_top_level_health_endpoint(client: TestClient):
    """
    Test that GET /health returns 200 OK and {'status': 'ok'}.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_v1_health_endpoint(client: TestClient):
    """
    Test that GET /api/v1/health returns 200 OK and detailed service metadata.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "aura-workforce-api"
    assert data["checks"]["database"] == "ok"


def test_production_secret_key_guard():
    """
    Ensure settings refuse to initialize with default SECRET_KEY when ENV=production.
    """
    import pytest
    from app.core.config import Settings

    with pytest.raises(ValueError, match="Default SECRET_KEY/JWT_SECRET is forbidden"):
        Settings(ENV="production")

    # Providing a real secret passes
    valid_settings = Settings(ENV="production", JWT_SECRET="a-very-strong-unique-production-secret-123456789")
    assert valid_settings.ENV == "production"
