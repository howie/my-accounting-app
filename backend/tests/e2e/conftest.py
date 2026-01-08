"""E2E test fixtures and helpers."""

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient


class E2ETestHelper:
    """Helper class for E2E test operations."""

    def __init__(self, client: TestClient):
        self.client = client
        self.user_id: str | None = None
        self.ledger_id: str | None = None

    def setup_user(self, email: str = "e2e-test@example.com") -> dict[str, Any]:
        """Create or get a user and set up headers."""
        response = self.client.post("/api/v1/users/setup", json={"email": email})
        assert response.status_code in (200, 201), f"User setup failed: {response.text}"
        user = response.json()
        self.user_id = user["id"]
        return user

    def create_ledger(
        self, name: str = "Test Ledger", initial_balance: float = 1000.0
    ) -> dict[str, Any]:
        """Create a ledger."""
        assert self.user_id, "Must call setup_user first"
        response = self.client.post(
            "/api/v1/ledgers",
            json={"name": name, "initial_balance": initial_balance},
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 201, f"Ledger creation failed: {response.text}"
        ledger = response.json()
        self.ledger_id = ledger["id"]
        return ledger

    def get_ledger(self, ledger_id: str | None = None) -> dict[str, Any]:
        """Get a ledger."""
        lid = ledger_id or self.ledger_id
        assert lid, "No ledger ID"
        response = self.client.get(
            f"/api/v1/ledgers/{lid}",
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 200, f"Get ledger failed: {response.text}"
        return response.json()

    def list_ledgers(self) -> list[dict[str, Any]]:
        """List all ledgers for user."""
        response = self.client.get(
            "/api/v1/ledgers",
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 200, f"List ledgers failed: {response.text}"
        return response.json()["data"]

    def delete_ledger(self, ledger_id: str | None = None) -> None:
        """Delete a ledger."""
        lid = ledger_id or self.ledger_id
        response = self.client.delete(
            f"/api/v1/ledgers/{lid}",
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 204, f"Delete ledger failed: {response.text}"

    def create_account(
        self,
        name: str,
        account_type: str,
        parent_id: str | None = None,
        ledger_id: str | None = None,
    ) -> dict[str, Any]:
        """Create an account."""
        lid = ledger_id or self.ledger_id
        assert lid, "No ledger ID"
        data: dict[str, Any] = {"name": name, "type": account_type}
        if parent_id:
            data["parent_id"] = parent_id
        response = self.client.post(
            f"/api/v1/ledgers/{lid}/accounts",
            json=data,
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 201, f"Account creation failed: {response.text}"
        return response.json()

    def list_accounts(self, ledger_id: str | None = None) -> list[dict[str, Any]]:
        """List accounts (flat)."""
        lid = ledger_id or self.ledger_id
        response = self.client.get(
            f"/api/v1/ledgers/{lid}/accounts",
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 200, f"List accounts failed: {response.text}"
        return response.json()["data"]

    def get_account_tree(self, ledger_id: str | None = None) -> list[dict[str, Any]]:
        """Get account tree (hierarchical)."""
        lid = ledger_id or self.ledger_id
        response = self.client.get(
            f"/api/v1/ledgers/{lid}/accounts/tree",
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 200, f"Get account tree failed: {response.text}"
        return response.json()["data"]

    def get_account(self, account_id: str, ledger_id: str | None = None) -> dict[str, Any]:
        """Get a single account."""
        lid = ledger_id or self.ledger_id
        response = self.client.get(
            f"/api/v1/ledgers/{lid}/accounts/{account_id}",
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 200, f"Get account failed: {response.text}"
        return response.json()

    def delete_account(
        self, account_id: str, ledger_id: str | None = None, expect_success: bool = True
    ) -> int:
        """Delete an account. Returns status code."""
        lid = ledger_id or self.ledger_id
        response = self.client.delete(
            f"/api/v1/ledgers/{lid}/accounts/{account_id}",
            headers={"X-User-ID": self.user_id},
        )
        if expect_success:
            assert response.status_code == 204, f"Delete account failed: {response.text}"
        return response.status_code

    def create_transaction(
        self,
        from_account_id: str,
        to_account_id: str,
        amount: float,
        transaction_type: str,
        description: str = "Test transaction",
        date: str = "2024-01-15",
        ledger_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a transaction."""
        lid = ledger_id or self.ledger_id
        response = self.client.post(
            f"/api/v1/ledgers/{lid}/transactions",
            json={
                "from_account_id": from_account_id,
                "to_account_id": to_account_id,
                "amount": amount,
                "transaction_type": transaction_type,
                "description": description,
                "date": date,
            },
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 201, f"Transaction creation failed: {response.text}"
        return response.json()

    def list_transactions(
        self,
        ledger_id: str | None = None,
        search: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        account_id: str | None = None,
        transaction_type: str | None = None,
    ) -> dict[str, Any]:
        """List transactions with optional filters."""
        lid = ledger_id or self.ledger_id
        params: dict[str, str] = {}
        if search:
            params["search"] = search
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        if account_id:
            params["account_id"] = account_id
        if transaction_type:
            params["transaction_type"] = transaction_type

        response = self.client.get(
            f"/api/v1/ledgers/{lid}/transactions",
            params=params,
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 200, f"List transactions failed: {response.text}"
        return response.json()

    def get_transaction(
        self, transaction_id: str, ledger_id: str | None = None
    ) -> dict[str, Any]:
        """Get a single transaction."""
        lid = ledger_id or self.ledger_id
        response = self.client.get(
            f"/api/v1/ledgers/{lid}/transactions/{transaction_id}",
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 200, f"Get transaction failed: {response.text}"
        return response.json()

    def update_transaction(
        self,
        transaction_id: str,
        from_account_id: str,
        to_account_id: str,
        amount: float,
        transaction_type: str,
        description: str,
        date: str,
        ledger_id: str | None = None,
    ) -> dict[str, Any]:
        """Update a transaction."""
        lid = ledger_id or self.ledger_id
        response = self.client.put(
            f"/api/v1/ledgers/{lid}/transactions/{transaction_id}",
            json={
                "from_account_id": from_account_id,
                "to_account_id": to_account_id,
                "amount": amount,
                "transaction_type": transaction_type,
                "description": description,
                "date": date,
            },
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 200, f"Transaction update failed: {response.text}"
        return response.json()

    def delete_transaction(
        self, transaction_id: str, ledger_id: str | None = None
    ) -> None:
        """Delete a transaction."""
        lid = ledger_id or self.ledger_id
        response = self.client.delete(
            f"/api/v1/ledgers/{lid}/transactions/{transaction_id}",
            headers={"X-User-ID": self.user_id},
        )
        assert response.status_code == 204, f"Delete transaction failed: {response.text}"

    def find_account_by_name(
        self, name: str, accounts: list[dict[str, Any]] | None = None
    ) -> dict[str, Any] | None:
        """Find an account by name in a list."""
        if accounts is None:
            accounts = self.list_accounts()
        for acc in accounts:
            if acc["name"] == name:
                return acc
        return None


@pytest.fixture
def e2e_helper(client: TestClient) -> E2ETestHelper:
    """Create an E2E test helper instance."""
    return E2ETestHelper(client)


@pytest.fixture
def setup_user_and_ledger(e2e_helper: E2ETestHelper) -> E2ETestHelper:
    """Set up a user and ledger for testing."""
    e2e_helper.setup_user(f"e2e-{uuid.uuid4()}@example.com")
    e2e_helper.create_ledger("E2E Test Ledger", 5000.0)
    return e2e_helper
