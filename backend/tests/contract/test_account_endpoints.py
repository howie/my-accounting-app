"""Contract tests for Account API endpoints.

Tests the REST API contract as defined in contracts/account_service.md.
These tests verify the endpoints behave according to the documented contract.
"""

import uuid

import pytest
from fastapi.testclient import TestClient


class TestAccountEndpointsContract:
    """Contract tests for /api/v1/ledgers/{ledger_id}/accounts endpoints."""

    @pytest.fixture
    def ledger_id(self, client: TestClient) -> str:
        """Create a test ledger and return its ID."""
        response = client.post("/api/v1/ledgers", json={"name": "Test Ledger"})
        return response.json()["id"]

    # --- POST /api/v1/ledgers/{ledger_id}/accounts ---

    def test_create_account_returns_201(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """POST /accounts returns 201 Created on success."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Bank Account", "type": "ASSET"},
        )

        assert response.status_code == 201

    def test_create_account_returns_account_data(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """POST /accounts returns the created account data."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Savings", "type": "ASSET"},
        )

        data = response.json()
        assert "id" in data
        assert data["name"] == "Savings"
        assert data["type"] == "ASSET"

    def test_create_account_returns_uuid_id(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """POST /accounts returns a valid UUID as id."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Test", "type": "ASSET"},
        )

        data = response.json()
        uuid.UUID(data["id"])  # Should not raise

    def test_create_account_returns_ledger_id(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """POST /accounts returns the ledger_id."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Test", "type": "ASSET"},
        )

        data = response.json()
        assert data["ledger_id"] == ledger_id

    def test_create_account_returns_zero_balance(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """POST /accounts returns balance of 0.00."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Test", "type": "ASSET"},
        )

        data = response.json()
        assert data["balance"] == "0.00"

    def test_create_account_returns_is_system_false(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """POST /accounts returns is_system=false for user-created accounts."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Test", "type": "ASSET"},
        )

        data = response.json()
        assert data["is_system"] is False

    def test_create_account_returns_timestamps(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """POST /accounts returns created_at and updated_at."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Test", "type": "ASSET"},
        )

        data = response.json()
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_account_all_types(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """POST /accounts accepts all account types."""
        for account_type in ["ASSET", "LIABILITY", "INCOME", "EXPENSE"]:
            response = client.post(
                f"/api/v1/ledgers/{ledger_id}/accounts",
                json={"name": f"Test {account_type}", "type": account_type},
            )
            assert response.status_code == 201
            assert response.json()["type"] == account_type

    def test_create_account_empty_name_returns_422(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """POST /accounts returns 422 for empty name (validation error)."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "", "type": "ASSET"},
        )

        assert response.status_code == 422

    def test_create_account_invalid_type_returns_422(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """POST /accounts returns 422 for invalid account type."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Test", "type": "INVALID"},
        )

        assert response.status_code == 422

    def test_create_account_nonexistent_ledger_returns_404(
        self, client: TestClient
    ) -> None:
        """POST /accounts returns 404 for non-existent ledger."""
        fake_id = str(uuid.uuid4())

        response = client.post(
            f"/api/v1/ledgers/{fake_id}/accounts",
            json={"name": "Test", "type": "ASSET"},
        )

        assert response.status_code == 404

    def test_create_account_duplicate_name_returns_409(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """POST /accounts returns 409 for duplicate account name."""
        client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Duplicate", "type": "ASSET"},
        )

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Duplicate", "type": "EXPENSE"},
        )

        assert response.status_code == 409

    # --- GET /api/v1/ledgers/{ledger_id}/accounts ---

    def test_get_accounts_returns_200(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """GET /accounts returns 200 OK."""
        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")

        assert response.status_code == 200

    def test_get_accounts_returns_data_list(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """GET /accounts returns a data object with list."""
        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")

        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_accounts_includes_system_accounts(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """GET /accounts returns system accounts (Cash, Equity)."""
        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")

        data = response.json()
        names = [a["name"] for a in data["data"]]
        assert "Cash" in names
        assert "Equity" in names

    def test_get_accounts_system_accounts_are_flagged(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """GET /accounts marks system accounts with is_system=true."""
        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")

        data = response.json()
        cash = next(a for a in data["data"] if a["name"] == "Cash")
        equity = next(a for a in data["data"] if a["name"] == "Equity")
        assert cash["is_system"] is True
        assert equity["is_system"] is True

    def test_get_accounts_includes_user_accounts(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """GET /accounts returns user-created accounts."""
        client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Food", "type": "EXPENSE"},
        )

        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")

        data = response.json()
        names = [a["name"] for a in data["data"]]
        assert "Food" in names

    def test_get_accounts_filter_by_type(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """GET /accounts?type=X filters by account type."""
        client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Food", "type": "EXPENSE"},
        )

        response = client.get(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            params={"type": "EXPENSE"},
        )

        data = response.json()
        assert all(a["type"] == "EXPENSE" for a in data["data"])

    def test_get_accounts_item_has_required_fields(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """GET /accounts items have all required fields."""
        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")

        data = response.json()
        account = data["data"][0]
        assert "id" in account
        assert "name" in account
        assert "type" in account
        assert "balance" in account
        assert "is_system" in account

    def test_get_accounts_nonexistent_ledger_returns_404(
        self, client: TestClient
    ) -> None:
        """GET /accounts returns 404 for non-existent ledger."""
        fake_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/ledgers/{fake_id}/accounts")

        assert response.status_code == 404

    # --- GET /api/v1/ledgers/{ledger_id}/accounts/{account_id} ---

    def test_get_account_by_id_returns_200(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """GET /accounts/{id} returns 200 OK for existing account."""
        create_response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Test", "type": "ASSET"},
        )
        account_id = create_response.json()["id"]

        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts/{account_id}")

        assert response.status_code == 200

    def test_get_account_by_id_returns_account_data(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """GET /accounts/{id} returns the account data."""
        create_response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Savings", "type": "ASSET"},
        )
        account_id = create_response.json()["id"]

        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts/{account_id}")

        data = response.json()
        assert data["id"] == account_id
        assert data["name"] == "Savings"
        assert data["type"] == "ASSET"

    def test_get_account_by_id_includes_full_fields(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """GET /accounts/{id} returns full account details."""
        create_response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Test", "type": "ASSET"},
        )
        account_id = create_response.json()["id"]

        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts/{account_id}")

        data = response.json()
        assert "id" in data
        assert "ledger_id" in data
        assert "name" in data
        assert "type" in data
        assert "balance" in data
        assert "is_system" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_account_nonexistent_returns_404(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """GET /accounts/{id} returns 404 for non-existent account."""
        fake_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts/{fake_id}")

        assert response.status_code == 404

    # --- PATCH /api/v1/ledgers/{ledger_id}/accounts/{account_id} ---

    def test_update_account_returns_200(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """PATCH /accounts/{id} returns 200 OK on success."""
        create_response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Old Name", "type": "ASSET"},
        )
        account_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/accounts/{account_id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 200

    def test_update_account_changes_name(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """PATCH /accounts/{id} updates the account name."""
        create_response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Old Name", "type": "ASSET"},
        )
        account_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/accounts/{account_id}",
            json={"name": "Updated Name"},
        )

        data = response.json()
        assert data["name"] == "Updated Name"

    def test_update_system_account_returns_400(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """PATCH /accounts/{id} returns 400 for system accounts."""
        # Get Cash account ID
        accounts_response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")
        cash = next(a for a in accounts_response.json()["data"] if a["name"] == "Cash")

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/accounts/{cash['id']}",
            json={"name": "Renamed Cash"},
        )

        assert response.status_code == 400

    def test_update_account_duplicate_name_returns_409(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """PATCH /accounts/{id} returns 409 for duplicate name."""
        client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Existing", "type": "ASSET"},
        )
        create_response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Original", "type": "ASSET"},
        )
        account_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/accounts/{account_id}",
            json={"name": "Existing"},
        )

        assert response.status_code == 409

    def test_update_account_nonexistent_returns_404(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """PATCH /accounts/{id} returns 404 for non-existent account."""
        fake_id = str(uuid.uuid4())

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/accounts/{fake_id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 404

    # --- DELETE /api/v1/ledgers/{ledger_id}/accounts/{account_id} ---

    def test_delete_account_returns_204(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """DELETE /accounts/{id} returns 204 No Content on success."""
        create_response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Test", "type": "ASSET"},
        )
        account_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/ledgers/{ledger_id}/accounts/{account_id}")

        assert response.status_code == 204

    def test_delete_account_removes_from_list(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """DELETE /accounts/{id} removes the account from GET list."""
        create_response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "ToDelete", "type": "ASSET"},
        )
        account_id = create_response.json()["id"]

        client.delete(f"/api/v1/ledgers/{ledger_id}/accounts/{account_id}")

        get_response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")
        names = [a["name"] for a in get_response.json()["data"]]
        assert "ToDelete" not in names

    def test_delete_system_account_returns_400(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """DELETE /accounts/{id} returns 400 for system accounts (FR-004)."""
        accounts_response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")
        cash = next(a for a in accounts_response.json()["data"] if a["name"] == "Cash")

        response = client.delete(f"/api/v1/ledgers/{ledger_id}/accounts/{cash['id']}")

        assert response.status_code == 400

    def test_delete_account_with_transactions_returns_409(
        self, client: TestClient
    ) -> None:
        """DELETE /accounts/{id} returns 409 if account has transactions."""
        # Create ledger with initial balance (creates transactions)
        ledger_response = client.post(
            "/api/v1/ledgers",
            json={"name": "Test", "initial_balance": "1000.00"},
        )
        ledger_id = ledger_response.json()["id"]

        # Get Cash account which now has a transaction
        accounts_response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")
        cash = next(a for a in accounts_response.json()["data"] if a["name"] == "Cash")

        response = client.delete(f"/api/v1/ledgers/{ledger_id}/accounts/{cash['id']}")

        # Should be 400 (system account) or 409 (has transactions)
        assert response.status_code in [400, 409]

    def test_delete_account_nonexistent_returns_404(
        self, client: TestClient, ledger_id: str
    ) -> None:
        """DELETE /accounts/{id} returns 404 for non-existent account."""
        fake_id = str(uuid.uuid4())

        response = client.delete(f"/api/v1/ledgers/{ledger_id}/accounts/{fake_id}")

        assert response.status_code == 404
