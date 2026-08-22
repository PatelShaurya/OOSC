from fastapi.testclient import TestClient


def test_auth_me_unauthorized(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_auth_me_authorized(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == "user123"


def test_update_profile(client: TestClient, auth_headers: dict):
    payload = {
        "full_name": "Rohan Sharma",
        "state": "Maharashtra",
        "district": "Mumbai City",
        "preferred_language": "hi",
    }
    response = client.patch("/api/v1/auth/profile", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["full_name"] == "Rohan Sharma"
    assert data["data"]["state"] == "Maharashtra"
    assert data["data"]["preferred_language"] == "hi"
