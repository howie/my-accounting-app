"""Contract tests for Ledger API endpoints.

Tests the REST API contract as defined in contracts/ledger_service.md.
These tests verify the endpoints behave according to the documented contract.
"""

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient


class TestLedgerEndpointsContract:
    """Contract tests for /api/v1/ledgers endpoints."""

    # --- POST /api/v1/ledgers ---

    def test_create_ledger_returns_201(self, client: TestClient) -> None:
        """POST /api/v1/ledgers returns 201 Created on success."""
        response = client.post(
            "/api/v1/ledgers",
            json={"name": "Test Ledger", "initial_balance": "1000.00"},
        )

        assert response.status_code == 201

    def test_create_ledger_returns_ledger_data(self, client: TestClient) -> None:
        """POST /api/v1/ledgers returns the created ledger data."""
        response = client.post(
            "/api/v1/ledgers",
            json={"name": "My Budget", "initial_balance": "5000.00"},
        )

        data = response.json()
        assert "id" in data
        assert data["name"] == "My Budget"
        assert data["initial_balance"] == "5000.00"

    def test_create_ledger_returns_uuid_id(self, client: TestClient) -> None:
        """POST /api/v1/ledgers returns a valid UUID as id."""
        response = client.post(
            "/api/v1/ledgers",
            json={"name": "Test"},
        )

        data = response.json()
        # Should not raise
        uuid.UUID(data["id"])

    def test_create_ledger_returns_user_id(self, client: TestClient) -> None:
        """POST /api/v1/ledgers returns the user_id."""
        response = client.post(
            "/api/v1/ledgers",
            json={"name": "Test"},
        )

        data = response.json()
        assert "user_id" in data
        # Should not raise
        uuid.UUID(data["user_id"])

    def test_create_ledger_returns_created_at(self, client: TestClient) -> None:
        """POST /api/v1/ledgers returns created_at timestamp."""
        response = client.post(
            "/api/v1/ledgers",
            json={"name": "Test"},
        )

        data = response.json()
        assert "created_at" in data
        assert data["created_at"] is not None

    def test_create_ledger_default_initial_balance(self, client: TestClient) -> None:
        """POST /api/v1/ledgers defaults initial_balance to 0."""
        response = client.post(
            "/api/v1/ledgers",
            json={"name": "Test"},
        )

        data = response.json()
        assert data["initial_balance"] == "0.00"

    def test_create_ledger_empty_name_returns_422(self, client: TestClient) -> None:
        """POST /api/v1/ledgers returns 422 for empty name (validation error)."""
        response = client.post(
            "/api/v1/ledgers",
            json={"name": "", "initial_balance": "1000.00"},
        )

        assert response.status_code == 422

    def test_create_ledger_negative_balance_returns_422(self, client: TestClient) -> None:
        """POST /api/v1/ledgers returns 422 for negative initial_balance (validation error)."""
        response = client.post(
            "/api/v1/ledgers",
            json={"name": "Test", "initial_balance": "-100.00"},
        )

        assert response.status_code == 422

    def test_create_ledger_missing_name_returns_422(self, client: TestClient) -> None:
        """POST /api/v1/ledgers returns 422 for missing name field."""
        response = client.post(
            "/api/v1/ledgers",
            json={"initial_balance": "1000.00"},
        )

        assert response.status_code == 422

    # --- GET /api/v1/ledgers ---

    def test_get_ledgers_returns_200(self, client: TestClient) -> None:
        """GET /api/v1/ledgers returns 200 OK."""
        response = client.get("/api/v1/ledgers")

        assert response.status_code == 200

    def test_get_ledgers_returns_data_list(self, client: TestClient) -> None:
        """GET /api/v1/ledgers returns a data object with list."""
        response = client.get("/api/v1/ledgers")

        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_ledgers_returns_empty_for_new_user(self, client: TestClient) -> None:
        """GET /api/v1/ledgers returns empty list for user with no ledgers."""
        response = client.get("/api/v1/ledgers")

        data = response.json()
        assert data["data"] == []

    def test_get_ledgers_returns_created_ledgers(self, client: TestClient) -> None:
        """GET /api/v1/ledgers returns ledgers after creation."""
        client.post("/api/v1/ledgers", json={"name": "Ledger 1"})
        client.post("/api/v1/ledgers", json={"name": "Ledger 2"})

        response = client.get("/api/v1/ledgers")

        data = response.json()
        assert len(data["data"]) == 2
        names = [l["name"] for l in data["data"]]
        assert "Ledger 1" in names
        assert "Ledger 2" in names

    def test_get_ledgers_item_has_required_fields(self, client: TestClient) -> None:
        """GET /api/v1/ledgers items have all required fields."""
        client.post("/api/v1/ledgers", json={"name": "Test"})

        response = client.get("/api/v1/ledgers")

        data = response.json()
        ledger = data["data"][0]
        assert "id" in ledger
        assert "name" in ledger
        assert "initial_balance" in ledger
        assert "created_at" in ledger

    # --- GET /api/v1/ledgers/{ledger_id} ---

    def test_get_ledger_by_id_returns_200(self, client: TestClient) -> None:
        """GET /api/v1/ledgers/{id} returns 200 OK for existing ledger."""
        create_response = client.post("/api/v1/ledgers", json={"name": "Test"})
        ledger_id = create_response.json()["id"]

        response = client.get(f"/api/v1/ledgers/{ledger_id}")

        assert response.status_code == 200

    def test_get_ledger_by_id_returns_ledger_data(self, client: TestClient) -> None:
        """GET /api/v1/ledgers/{id} returns the ledger data."""
        create_response = client.post(
            "/api/v1/ledgers",
            json={"name": "My Budget", "initial_balance": "2500.00"},
        )
        ledger_id = create_response.json()["id"]

        response = client.get(f"/api/v1/ledgers/{ledger_id}")

        data = response.json()
        assert data["id"] == ledger_id
        assert data["name"] == "My Budget"
        assert data["initial_balance"] == "2500.00"

    def test_get_ledger_by_id_includes_user_id(self, client: TestClient) -> None:
        """GET /api/v1/ledgers/{id} returns user_id."""
        create_response = client.post("/api/v1/ledgers", json={"name": "Test"})
        ledger_id = create_response.json()["id"]

        response = client.get(f"/api/v1/ledgers/{ledger_id}")

        data = response.json()
        assert "user_id" in data

    def test_get_ledger_nonexistent_returns_404(self, client: TestClient) -> None:
        """GET /api/v1/ledgers/{id} returns 404 for non-existent ledger."""
        fake_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/ledgers/{fake_id}")

        assert response.status_code == 404

    def test_get_ledger_invalid_uuid_returns_422(self, client: TestClient) -> None:
        """GET /api/v1/ledgers/{id} returns 422 for invalid UUID."""
        response = client.get("/api/v1/ledgers/not-a-uuid")

        assert response.status_code == 422

    # --- PATCH /api/v1/ledgers/{ledger_id} ---

    def test_update_ledger_returns_200(self, client: TestClient) -> None:
        """PATCH /api/v1/ledgers/{id} returns 200 OK on success."""
        create_response = client.post("/api/v1/ledgers", json={"name": "Old Name"})
        ledger_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 200

    def test_update_ledger_changes_name(self, client: TestClient) -> None:
        """PATCH /api/v1/ledgers/{id} updates the ledger name."""
        create_response = client.post("/api/v1/ledgers", json={"name": "Old Name"})
        ledger_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}",
            json={"name": "Updated Name"},
        )

        data = response.json()
        assert data["name"] == "Updated Name"

    def test_update_ledger_preserves_initial_balance(self, client: TestClient) -> None:
        """PATCH /api/v1/ledgers/{id} does not change initial_balance."""
        create_response = client.post(
            "/api/v1/ledgers",
            json={"name": "Test", "initial_balance": "5000.00"},
        )
        ledger_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}",
            json={"name": "Updated"},
        )

        data = response.json()
        assert data["initial_balance"] == "5000.00"

    def test_update_ledger_nonexistent_returns_404(self, client: TestClient) -> None:
        """PATCH /api/v1/ledgers/{id} returns 404 for non-existent ledger."""
        fake_id = str(uuid.uuid4())

        response = client.patch(
            f"/api/v1/ledgers/{fake_id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 404

    def test_update_ledger_empty_name_returns_422(self, client: TestClient) -> None:
        """PATCH /api/v1/ledgers/{id} returns 422 for empty name (validation error)."""
        create_response = client.post("/api/v1/ledgers", json={"name": "Test"})
        ledger_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}",
            json={"name": ""},
        )

        assert response.status_code == 422

    # --- DELETE /api/v1/ledgers/{ledger_id} ---

    def test_delete_ledger_returns_204(self, client: TestClient) -> None:
        """DELETE /api/v1/ledgers/{id} returns 204 No Content on success."""
        create_response = client.post("/api/v1/ledgers", json={"name": "Test"})
        ledger_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/ledgers/{ledger_id}")

        assert response.status_code == 204

    def test_delete_ledger_removes_from_list(self, client: TestClient) -> None:
        """DELETE /api/v1/ledgers/{id} removes the ledger from GET list."""
        create_response = client.post("/api/v1/ledgers", json={"name": "Test"})
        ledger_id = create_response.json()["id"]

        client.delete(f"/api/v1/ledgers/{ledger_id}")

        get_response = client.get("/api/v1/ledgers")
        data = get_response.json()
        assert len(data["data"]) == 0

    def test_delete_ledger_makes_get_return_404(self, client: TestClient) -> None:
        """DELETE /api/v1/ledgers/{id} makes subsequent GET return 404."""
        create_response = client.post("/api/v1/ledgers", json={"name": "Test"})
        ledger_id = create_response.json()["id"]

        client.delete(f"/api/v1/ledgers/{ledger_id}")

        get_response = client.get(f"/api/v1/ledgers/{ledger_id}")
        assert get_response.status_code == 404

    def test_delete_ledger_nonexistent_returns_404(self, client: TestClient) -> None:
        """DELETE /api/v1/ledgers/{id} returns 404 for non-existent ledger."""
        fake_id = str(uuid.uuid4())

        response = client.delete(f"/api/v1/ledgers/{fake_id}")

        assert response.status_code == 404
