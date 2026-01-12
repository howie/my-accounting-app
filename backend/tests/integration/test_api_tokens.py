"""Integration tests for API Token REST endpoints.

Tests the full HTTP flow for token management.
"""

import uuid

from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.models.user import User


class TestListTokensEndpoint:
    """Test GET /api/v1/tokens endpoint."""

    def test_list_tokens_returns_empty_list(self, client: TestClient, session: Session):
        """List tokens should return empty list when no tokens exist."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        response = client.get(
            "/api/v1/tokens",
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["tokens"] == []

    def test_list_tokens_returns_user_tokens(self, client: TestClient, session: Session):
        """List tokens should return the user's tokens."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create a token first
        create_response = client.post(
            "/api/v1/tokens",
            json={"name": "Claude Desktop"},
            headers={"X-User-ID": str(user.id)},
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        response = client.get(
            "/api/v1/tokens",
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["tokens"]) == 1
        assert data["tokens"][0]["name"] == "Claude Desktop"
        # Should not return full token
        assert "token" not in data["tokens"][0]
        # Should return prefix
        assert "token_prefix" in data["tokens"][0]


class TestCreateTokenEndpoint:
    """Test POST /api/v1/tokens endpoint."""

    def test_create_token_success(self, client: TestClient, session: Session):
        """Create token should return the full token once."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        response = client.post(
            "/api/v1/tokens",
            json={"name": "Claude Desktop"},
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["name"] == "Claude Desktop"
        assert "token" in data
        assert data["token"].startswith("ldo_")
        assert len(data["token"]) == 52
        assert "token_prefix" in data
        assert data["token_prefix"] == data["token"][:8]
        assert "message" in data

    def test_create_token_without_name_fails(self, client: TestClient, session: Session):
        """Create token without name should fail."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        response = client.post(
            "/api/v1/tokens",
            json={},
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_token_with_empty_name_fails(self, client: TestClient, session: Session):
        """Create token with empty name should fail."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        response = client.post(
            "/api/v1/tokens",
            json={"name": ""},
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_token_with_long_name_fails(self, client: TestClient, session: Session):
        """Create token with name > 100 chars should fail."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        response = client.post(
            "/api/v1/tokens",
            json={"name": "a" * 101},
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRevokeTokenEndpoint:
    """Test DELETE /api/v1/tokens/{token_id} endpoint."""

    def test_revoke_token_success(self, client: TestClient, session: Session):
        """Revoke token should soft delete the token."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create a token first
        create_response = client.post(
            "/api/v1/tokens",
            json={"name": "Claude Desktop"},
            headers={"X-User-ID": str(user.id)},
        )
        token_id = create_response.json()["id"]

        response = client.delete(
            f"/api/v1/tokens/{token_id}",
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == token_id
        assert "revoked_at" in data
        assert "message" in data

    def test_revoke_nonexistent_token_returns_404(self, client: TestClient, session: Session):
        """Revoking nonexistent token should return 404."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/v1/tokens/{fake_id}",
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_revoke_other_users_token_returns_404(self, client: TestClient, session: Session):
        """Revoking another user's token should return 404."""
        user1 = User(email="user1@example.com", display_name="User 1")
        user2 = User(email="user2@example.com", display_name="User 2")
        session.add(user1)
        session.add(user2)
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        # Create token for user 1
        create_response = client.post(
            "/api/v1/tokens",
            json={"name": "User 1 Token"},
            headers={"X-User-ID": str(user1.id)},
        )
        token_id = create_response.json()["id"]

        # User 2 tries to revoke
        response = client.delete(
            f"/api/v1/tokens/{token_id}",
            headers={"X-User-ID": str(user2.id)},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_revoked_token_not_in_list(self, client: TestClient, session: Session):
        """Revoked token should not appear in list."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create and revoke a token
        create_response = client.post(
            "/api/v1/tokens",
            json={"name": "Claude Desktop"},
            headers={"X-User-ID": str(user.id)},
        )
        token_id = create_response.json()["id"]

        client.delete(
            f"/api/v1/tokens/{token_id}",
            headers={"X-User-ID": str(user.id)},
        )

        # List should be empty
        response = client.get(
            "/api/v1/tokens",
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["tokens"] == []
