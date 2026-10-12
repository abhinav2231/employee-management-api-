import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Test client fixture providing a synchronous HTTP client for tests.
    """
    with TestClient(app) as test_client:
        yield test_client
