"""Contract tests for User API endpoints.

Tests the REST API contract as defined in contracts/user_account_service.md.
These tests verify the endpoints behave according to the documented contract.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.models.user import User


class TestUserEndpointsContract:
    """Contract tests for /api/v1/users endpoints."""

    # --- GET /api/v1/users/me ---

    def test_get_me_returns_200(self, client: TestClient) -> None:
        """GET /api/v1/users/me returns 200 OK."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 200

    def test_get_me_returns_user_data(self, client: TestClient) -> None:
        """GET /api/v1/users/me returns user data."""
        response = client.get("/api/v1/users/me")

        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "created_at" in data

    def test_get_me_returns_valid_uuid_id(self, client: TestClient) -> None:
        """GET /api/v1/users/me returns a valid UUID as id."""
        response = client.get("/api/v1/users/me")

        data = response.json()
        # Should not raise
        uuid.UUID(data["id"])

    def test_get_me_creates_default_user_if_none(self, client: TestClient) -> None:
        """GET /api/v1/users/me creates default user if none exists."""
        response = client.get("/api/v1/users/me")

        data = response.json()
        assert data["email"] == "user@localhost"

    def test_get_me_returns_same_user_on_repeated_calls(
        self, client: TestClient
    ) -> None:
        """GET /api/v1/users/me returns the same user on repeated calls."""
        response1 = client.get("/api/v1/users/me")
        response2 = client.get("/api/v1/users/me")

        assert response1.json()["id"] == response2.json()["id"]

    # --- POST /api/v1/users/setup ---

    def test_setup_returns_201(self, client: TestClient) -> None:
        """POST /api/v1/users/setup returns 201 Created on success."""
        response = client.post(
            "/api/v1/users/setup",
            json={"email": "setup@example.com"},
        )

        assert response.status_code == 201

    def test_setup_returns_user_data(self, client: TestClient) -> None:
        """POST /api/v1/users/setup returns the created user data."""
        response = client.post(
            "/api/v1/users/setup",
            json={"email": "newuser@example.com"},
        )

        data = response.json()
        assert "id" in data
        assert data["email"] == "newuser@example.com"
        assert "created_at" in data

    def test_setup_returns_valid_uuid_id(self, client: TestClient) -> None:
        """POST /api/v1/users/setup returns a valid UUID as id."""
        response = client.post(
            "/api/v1/users/setup",
            json={"email": "uuid@example.com"},
        )

        data = response.json()
        # Should not raise
        uuid.UUID(data["id"])

    def test_setup_returns_409_if_user_exists(
        self, client: TestClient, session: Session
    ) -> None:
        """POST /api/v1/users/setup returns 409 Conflict if user already exists."""
        # Create existing user
        existing = User(email="existing@example.com")
        session.add(existing)
        session.commit()

        response = client.post(
            "/api/v1/users/setup",
            json={"email": "another@example.com"},
        )

        assert response.status_code == 409

    def test_setup_returns_422_for_invalid_email(self, client: TestClient) -> None:
        """POST /api/v1/users/setup returns 422 for missing email."""
        response = client.post(
            "/api/v1/users/setup",
            json={},
        )

        assert response.status_code == 422

    # --- Integration: Setup then Get Me ---

    def test_setup_then_get_me_returns_setup_user(self, client: TestClient) -> None:
        """After setup, get_me returns the setup user."""
        # Setup
        setup_response = client.post(
            "/api/v1/users/setup",
            json={"email": "myemail@example.com"},
        )
        setup_data = setup_response.json()

        # Get me
        me_response = client.get("/api/v1/users/me")
        me_data = me_response.json()

        assert me_data["id"] == setup_data["id"]
        assert me_data["email"] == "myemail@example.com"


class TestUserSetupStatus:
    """Tests for checking if user setup is needed."""

    def test_get_status_returns_200(self, client: TestClient) -> None:
        """GET /api/v1/users/status returns 200 OK."""
        response = client.get("/api/v1/users/status")
        assert response.status_code == 200

    def test_get_status_returns_setup_needed_true_when_no_user(
        self, client: TestClient
    ) -> None:
        """GET /api/v1/users/status returns setup_needed: true when no user."""
        response = client.get("/api/v1/users/status")

        data = response.json()
        assert data["setup_needed"] is True

    def test_get_status_returns_setup_needed_false_after_setup(
        self, client: TestClient
    ) -> None:
        """GET /api/v1/users/status returns setup_needed: false after setup."""
        # Setup user
        client.post(
            "/api/v1/users/setup",
            json={"email": "user@example.com"},
        )

        response = client.get("/api/v1/users/status")

        data = response.json()
        assert data["setup_needed"] is False
