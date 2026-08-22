import pytest
from fastapi.testclient import TestClient
from app.config import Settings, get_settings
from app.main import app


def get_test_settings() -> Settings:
    return Settings(
        PROJECT_NAME="CivicAI Backend [Test]",
        ENVIRONMENT="test",
        DEBUG=True,
        SUPABASE_URL="",
        SUPABASE_KEY="",
        SUPABASE_JWT_SECRET="test-secret-key-12345",
        RAG_SERVICE_URL="http://localhost:8001",
        RAG_API_KEY="",
    )


@pytest.fixture(scope="session")
def client() -> TestClient:
    app.dependency_overrides[get_settings] = get_test_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict:
    return {
        "Authorization": "Bearer test-user123",
        "Content-Type": "application/json",
    }


@pytest.fixture
def other_user_auth_headers() -> dict:
    return {
        "Authorization": "Bearer test-user456",
        "Content-Type": "application/json",
    }
