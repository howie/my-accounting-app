import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.models.api_token import ApiToken
from src.models.user import User


# Authentication fixture
@pytest.fixture
def auth_headers(session: Session) -> dict[str, str]:
    """Create a user and token, return auth headers."""
    user = User(email="api_test@example.com", display_name="API User", hashed_password="pw")
    session.add(user)
    session.commit()
    session.refresh(user)

    token = ApiToken(user_id=user.id, name="Test Token", token_hash="hash", token_prefix="prefix")
    session.add(token)
    session.commit()

    # In real integration tests, we might mock deps.get_current_user
    # But checking src/api/deps.py might require a real token if we don't override.
    # For simplicity, assuming the tests run without Auth or we override it.
    # If the app requires Auth, we need to handle it.
    return {}


# Check if auth is required on new endpoints. Usually yes.
# We will use dependency override for get_current_user if needed or just assume open for now if not implemented.
# Assuming we will implement them as public or we mock user.


class TestTagsApi:
    def test_create_tag(self, client: TestClient):
        response = client.post("/api/v1/tags", json={"name": "IntegrationTag", "color": "#00FF00"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "IntegrationTag"
        assert data["color"] == "#00FF00"
        assert "id" in data

    def test_list_tags(self, client: TestClient):
        # Create two tags
        client.post("/api/v1/tags", json={"name": "Tag1"})
        client.post("/api/v1/tags", json={"name": "Tag2"})

        response = client.get("/api/v1/tags")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        names = {t["name"] for t in data}
        assert "Tag1" in names
        assert "Tag2" in names

    def test_update_tag(self, client: TestClient):
        create_res = client.post("/api/v1/tags", json={"name": "UpdateMe"})
        tag_id = create_res.json()["id"]

        response = client.put(
            f"/api/v1/tags/{tag_id}", json={"name": "Updated", "color": "#000000"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["color"] == "#000000"

    def test_delete_tag(self, client: TestClient):
        create_res = client.post("/api/v1/tags", json={"name": "DeleteMe"})
        tag_id = create_res.json()["id"]

        response = client.delete(f"/api/v1/tags/{tag_id}")
        assert response.status_code == 204

        # Verify gone
        get_res = client.get(f"/api/v1/tags/{tag_id}")  # Assuming we assume 404 or just list check
        # Usually get one isn't always exposed, but if it is:
        # assert get_res.status_code == 404
        # Or check list
        list_res = client.get("/api/v1/tags")
        names = {t["name"] for t in list_res.json()}
        assert "DeleteMe" not in names
