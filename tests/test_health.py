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
    Test that GET /api/v1/health returns 200 OK and {'status': 'ok'}.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
