"""E2E tests for Account Management - Basic (TC-ACC-xxx).

Tests basic account CRUD operations.
"""

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from tests.e2e.conftest import E2ETestHelper


class TestAccountBasic:
    """TC-ACC: Account Basic tests."""

    def test_acc_001_create_root_expense_account(self, setup_user_and_ledger: E2ETestHelper):
        """TC-ACC-001: Create root EXPENSE account."""
        helper = setup_user_and_ledger

        account = helper.create_account("Food & Dining", "EXPENSE")

        assert account["name"] == "Food & Dining"
        assert account["type"] == "EXPENSE"
        assert account["depth"] == 1
        assert account["parent_id"] is None
        assert Decimal(account["balance"]) == Decimal("0.00")

    def test_acc_002_create_root_asset_account(self, setup_user_and_ledger: E2ETestHelper):
        """TC-ACC-002: Create root ASSET account."""
        helper = setup_user_and_ledger

        account = helper.create_account("Bank Account", "ASSET")

        assert account["name"] == "Bank Account"
        assert account["type"] == "ASSET"
        assert account["depth"] == 1

    def test_acc_003_create_root_income_account(self, setup_user_and_ledger: E2ETestHelper):
        """TC-ACC-003: Create root INCOME account."""
        helper = setup_user_and_ledger

        account = helper.create_account("Salary", "INCOME")

        assert account["name"] == "Salary"
        assert account["type"] == "INCOME"
        assert account["depth"] == 1

    def test_acc_004_create_root_liability_account(self, setup_user_and_ledger: E2ETestHelper):
        """TC-ACC-004: Create root LIABILITY account."""
        helper = setup_user_and_ledger

        account = helper.create_account("Credit Card", "LIABILITY")

        assert account["name"] == "Credit Card"
        assert account["type"] == "LIABILITY"
        assert account["depth"] == 1

    def test_acc_005_duplicate_name_same_type_rejected(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """TC-ACC-005: Duplicate account name within same ledger is rejected."""
        helper = setup_user_and_ledger

        # Create first account
        helper.create_account("Food", "EXPENSE")

        # Try to create duplicate
        response = client.post(
            f"/api/v1/ledgers/{helper.ledger_id}/accounts",
            json={"name": "Food", "type": "EXPENSE"},
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 409  # Conflict
        assert "already exists" in response.json()["detail"].lower()

    def test_acc_006_same_name_different_ledgers_allowed(self, e2e_helper: E2ETestHelper):
        """Same account name in different ledgers is allowed."""
        e2e_helper.setup_user(f"acc-test-{uuid.uuid4()}@example.com")

        # Create first ledger with account
        e2e_helper.create_ledger("Ledger One", 100.0)
        ledger1_id = e2e_helper.ledger_id
        e2e_helper.create_account("Groceries", "EXPENSE")

        # Create second ledger with same account name
        e2e_helper.create_ledger("Ledger Two", 200.0)
        account2 = e2e_helper.create_account("Groceries", "EXPENSE")

        # Should succeed
        assert account2["name"] == "Groceries"

    def test_acc_007_delete_leaf_account_no_transactions(
        self, setup_user_and_ledger: E2ETestHelper
    ):
        """TC-ACC-007: Delete leaf account with no transactions."""
        helper = setup_user_and_ledger

        account = helper.create_account("To Delete", "EXPENSE")
        account_id = account["id"]

        # Delete should succeed
        status = helper.delete_account(account_id)
        assert status == 204

        # Verify it's gone
        accounts = helper.list_accounts()
        account_ids = [a["id"] for a in accounts]
        assert account_id not in account_ids

    def test_acc_008_delete_system_account_rejected(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """TC-ACC-008: System accounts cannot be deleted."""
        helper = setup_user_and_ledger

        # Find Cash (system account)
        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        assert cash["is_system"] is True

        # Try to delete
        response = client.delete(
            f"/api/v1/ledgers/{helper.ledger_id}/accounts/{cash['id']}",
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 400
        assert "system account" in response.json()["detail"].lower()

    def test_acc_009_delete_account_with_transactions_rejected(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """TC-ACC-009: Account with transactions cannot be deleted."""
        helper = setup_user_and_ledger

        # Create expense account
        groceries = helper.create_account("Groceries", "EXPENSE")

        # Get Cash account
        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)

        # Create transaction
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
        )

        # Try to delete account with transaction
        response = client.delete(
            f"/api/v1/ledgers/{helper.ledger_id}/accounts/{groceries['id']}",
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 409
        assert "transaction" in response.json()["detail"].lower()

    def test_acc_010_update_account_name(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """Update account name."""
        helper = setup_user_and_ledger

        account = helper.create_account("Original", "EXPENSE")

        # Update name
        response = client.patch(
            f"/api/v1/ledgers/{helper.ledger_id}/accounts/{account['id']}",
            json={"name": "Updated Name"},
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 200
        updated = response.json()
        assert updated["name"] == "Updated Name"

    def test_acc_011_list_accounts_by_type(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """List accounts filtered by type."""
        helper = setup_user_and_ledger

        # Create accounts of different types
        helper.create_account("Food", "EXPENSE")
        helper.create_account("Transport", "EXPENSE")
        helper.create_account("Salary", "INCOME")

        # Filter by EXPENSE
        response = client.get(
            f"/api/v1/ledgers/{helper.ledger_id}/accounts?type=EXPENSE",
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 200
        accounts = response.json()["data"]

        # Should only have EXPENSE accounts
        for acc in accounts:
            assert acc["type"] == "EXPENSE"

    def test_acc_012_get_single_account(self, setup_user_and_ledger: E2ETestHelper):
        """Get single account by ID."""
        helper = setup_user_and_ledger

        created = helper.create_account("Test Account", "EXPENSE")

        # Fetch by ID
        account = helper.get_account(created["id"])

        assert account["id"] == created["id"]
        assert account["name"] == "Test Account"
        assert account["type"] == "EXPENSE"

    def test_acc_013_account_not_found(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """Accessing non-existent account returns 404."""
        helper = setup_user_and_ledger

        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/ledgers/{helper.ledger_id}/accounts/{fake_id}",
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 404

    def test_acc_014_empty_account_name_rejected(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """Empty account name is rejected."""
        helper = setup_user_and_ledger

        response = client.post(
            f"/api/v1/ledgers/{helper.ledger_id}/accounts",
            json={"name": "", "type": "EXPENSE"},
            headers={"X-User-ID": helper.user_id},
        )

        # 400 or 422 are both acceptable for validation errors
        assert response.status_code in (400, 422)
