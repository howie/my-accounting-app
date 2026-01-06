"""E2E tests for Ledger Management (TC-LDG-xxx).

Tests ledger CRUD operations and cascade behavior.
"""

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from tests.e2e.conftest import E2ETestHelper


class TestLedgerManagement:
    """TC-LDG: Ledger Management tests."""

    def test_ldg_001_create_ledger_with_initial_balance(self, e2e_helper: E2ETestHelper):
        """TC-LDG-001: Create ledger with initial balance creates system accounts."""
        e2e_helper.setup_user(f"ldg-test-{uuid.uuid4()}@example.com")

        # Create ledger with initial balance
        ledger = e2e_helper.create_ledger("My Personal Finance", 1000.0)

        assert ledger["name"] == "My Personal Finance"
        assert Decimal(ledger["initial_balance"]) == Decimal("1000.00")

        # Verify system accounts created
        accounts = e2e_helper.list_accounts()
        account_names = [a["name"] for a in accounts]

        assert "Cash" in account_names
        assert "Equity" in account_names

        # Cash account should have initial balance
        cash = e2e_helper.find_account_by_name("Cash", accounts)
        assert cash is not None
        assert cash["is_system"] is True
        assert Decimal(cash["balance"]) == Decimal("1000.00")

    def test_ldg_002_create_ledger_zero_balance(self, e2e_helper: E2ETestHelper):
        """TC-LDG-002: Create ledger with zero initial balance."""
        e2e_helper.setup_user(f"ldg-test-{uuid.uuid4()}@example.com")

        ledger = e2e_helper.create_ledger("Empty Ledger", 0.0)

        assert ledger["name"] == "Empty Ledger"
        assert Decimal(ledger["initial_balance"]) == Decimal("0.00")

        # Cash should have zero balance
        accounts = e2e_helper.list_accounts()
        cash = e2e_helper.find_account_by_name("Cash", accounts)
        assert Decimal(cash["balance"]) == Decimal("0.00")

    def test_ldg_003_view_ledger_list(self, e2e_helper: E2ETestHelper):
        """TC-LDG-003: View list of all user's ledgers."""
        e2e_helper.setup_user(f"ldg-test-{uuid.uuid4()}@example.com")

        # Create multiple ledgers
        e2e_helper.create_ledger("Ledger One", 100.0)
        e2e_helper.create_ledger("Ledger Two", 200.0)
        e2e_helper.create_ledger("Ledger Three", 300.0)

        # List should show all three
        ledgers = e2e_helper.list_ledgers()
        assert len(ledgers) == 3

        names = [l["name"] for l in ledgers]
        assert "Ledger One" in names
        assert "Ledger Two" in names
        assert "Ledger Three" in names

    def test_ldg_004_view_ledger_details(self, e2e_helper: E2ETestHelper):
        """TC-LDG-004: View single ledger with details."""
        e2e_helper.setup_user(f"ldg-test-{uuid.uuid4()}@example.com")
        created = e2e_helper.create_ledger("Detail Test Ledger", 500.0)

        # Fetch ledger details
        ledger = e2e_helper.get_ledger(created["id"])

        assert ledger["id"] == created["id"]
        assert ledger["name"] == "Detail Test Ledger"
        assert Decimal(ledger["initial_balance"]) == Decimal("500.00")
        assert "created_at" in ledger

    def test_ldg_005_delete_empty_ledger(self, e2e_helper: E2ETestHelper, client: TestClient):
        """TC-LDG-005: Delete ledger with only system accounts."""
        e2e_helper.setup_user(f"ldg-test-{uuid.uuid4()}@example.com")
        ledger = e2e_helper.create_ledger("To Delete", 100.0)
        ledger_id = ledger["id"]

        # Delete the ledger
        e2e_helper.delete_ledger(ledger_id)

        # Verify it's gone
        response = client.get(
            f"/api/v1/ledgers/{ledger_id}",
            headers={"X-User-ID": e2e_helper.user_id},
        )
        assert response.status_code == 404

    def test_ldg_006_delete_ledger_cascades(self, e2e_helper: E2ETestHelper, client: TestClient):
        """TC-LDG-006: Deleting ledger cascades to accounts and transactions."""
        e2e_helper.setup_user(f"ldg-test-{uuid.uuid4()}@example.com")
        ledger = e2e_helper.create_ledger("Cascade Test", 1000.0)

        # Create custom account
        groceries = e2e_helper.create_account("Groceries", "EXPENSE")

        # Get Cash account
        accounts = e2e_helper.list_accounts()
        cash = e2e_helper.find_account_by_name("Cash", accounts)

        # Create transaction
        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
        )

        ledger_id = ledger["id"]

        # Delete ledger
        e2e_helper.delete_ledger(ledger_id)

        # Ledger gone
        response = client.get(
            f"/api/v1/ledgers/{ledger_id}",
            headers={"X-User-ID": e2e_helper.user_id},
        )
        assert response.status_code == 404

    def test_ldg_007_update_ledger_name(self, e2e_helper: E2ETestHelper, client: TestClient):
        """Update ledger name."""
        e2e_helper.setup_user(f"ldg-test-{uuid.uuid4()}@example.com")
        ledger = e2e_helper.create_ledger("Original Name", 100.0)

        # Update name
        response = client.patch(
            f"/api/v1/ledgers/{ledger['id']}",
            json={"name": "Updated Name"},
            headers={"X-User-ID": e2e_helper.user_id},
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["name"] == "Updated Name"

    def test_ldg_008_duplicate_ledger_name_allowed(self, e2e_helper: E2ETestHelper):
        """Duplicate ledger names are allowed (same user can have multiple with same name)."""
        e2e_helper.setup_user(f"ldg-test-{uuid.uuid4()}@example.com")

        e2e_helper.create_ledger("Same Name", 100.0)
        # This should work - duplicate names allowed
        ledger2 = e2e_helper.create_ledger("Same Name", 200.0)

        assert ledger2["name"] == "Same Name"

    def test_ldg_009_ledger_not_found(self, e2e_helper: E2ETestHelper, client: TestClient):
        """Accessing non-existent ledger returns 404."""
        e2e_helper.setup_user(f"ldg-test-{uuid.uuid4()}@example.com")

        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/ledgers/{fake_id}",
            headers={"X-User-ID": e2e_helper.user_id},
        )
        assert response.status_code == 404
