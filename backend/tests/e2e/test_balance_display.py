"""E2E tests for Balance Display (TC-BAL-xxx).

Tests balance calculations and display.
"""

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from tests.e2e.conftest import E2ETestHelper


class TestBalanceDisplay:
    """TC-BAL: Balance Display tests."""

    def test_bal_001_initial_cash_balance(self, e2e_helper: E2ETestHelper):
        """TC-BAL-001: Cash account shows initial balance."""
        e2e_helper.setup_user(f"bal-test-{uuid.uuid4()}@example.com")
        e2e_helper.create_ledger("Balance Test", 1000.0)

        accounts = e2e_helper.list_accounts()
        cash = e2e_helper.find_account_by_name("Cash", accounts)

        assert Decimal(cash["balance"]) == Decimal("1000.00")

    def test_bal_002_balance_after_expense(self, setup_user_and_ledger: E2ETestHelper):
        """TC-BAL-002: Balance decreases after expense."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        initial_balance = Decimal(cash["balance"])

        groceries = helper.create_account("Groceries", "EXPENSE")

        # Create expense
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
        )

        # Verify balance decreased
        updated_cash = helper.get_account(cash["id"])
        assert Decimal(updated_cash["balance"]) == initial_balance - Decimal("50.00")

    def test_bal_003_negative_balance(self, e2e_helper: E2ETestHelper):
        """TC-BAL-003: Account can have negative balance."""
        e2e_helper.setup_user(f"bal-test-{uuid.uuid4()}@example.com")
        e2e_helper.create_ledger("Negative Test", 100.0)

        accounts = e2e_helper.list_accounts()
        cash = e2e_helper.find_account_by_name("Cash", accounts)

        groceries = e2e_helper.create_account("Groceries", "EXPENSE")

        # Spend more than available
        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=150.0,
            transaction_type="EXPENSE",
        )

        # Cash should be negative
        updated_cash = e2e_helper.get_account(cash["id"])
        assert Decimal(updated_cash["balance"]) == Decimal("-50.00")

    def test_bal_004_parent_aggregates_children(self, setup_user_and_ledger: E2ETestHelper):
        """TC-BAL-004: Parent balance is sum of children."""
        helper = setup_user_and_ledger

        # Create hierarchy
        food = helper.create_account("Food", "EXPENSE")
        groceries = helper.create_account("Groceries", "EXPENSE", parent_id=food["id"])
        restaurants = helper.create_account("Restaurants", "EXPENSE", parent_id=food["id"])

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)

        # Create transactions to children
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=100.0,
            transaction_type="EXPENSE",
        )
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=restaurants["id"],
            amount=75.0,
            transaction_type="EXPENSE",
        )

        # Get parent balance (should aggregate)
        parent = helper.get_account(food["id"])
        assert Decimal(parent["balance"]) == Decimal("175.00")

    def test_bal_005_balance_after_transaction_edit(self, setup_user_and_ledger: E2ETestHelper):
        """TC-BAL-005: Balance updates correctly after transaction edit."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        initial_cash = Decimal(cash["balance"])

        groceries = helper.create_account("Groceries", "EXPENSE")

        # Create transaction
        txn = helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
        )

        # Verify intermediate balance
        mid_cash = helper.get_account(cash["id"])
        assert Decimal(mid_cash["balance"]) == initial_cash - Decimal("50.00")

        # Update transaction to different amount
        helper.update_transaction(
            transaction_id=txn["id"],
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=30.0,
            transaction_type="EXPENSE",
            description="Updated",
            date="2024-01-15",
        )

        # Verify final balance reflects the update
        final_cash = helper.get_account(cash["id"])
        final_groceries = helper.get_account(groceries["id"])

        assert Decimal(final_cash["balance"]) == initial_cash - Decimal("30.00")
        assert Decimal(final_groceries["balance"]) == Decimal("30.00")

    def test_bal_006_balance_after_transaction_delete(self, setup_user_and_ledger: E2ETestHelper):
        """TC-BAL-006: Balance restores after transaction delete."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        initial_cash = Decimal(cash["balance"])

        groceries = helper.create_account("Groceries", "EXPENSE")

        # Create and delete transaction
        txn = helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
        )

        helper.delete_transaction(txn["id"])

        # Balance should be restored
        final_cash = helper.get_account(cash["id"])
        assert Decimal(final_cash["balance"]) == initial_cash

    def test_bal_007_multi_level_aggregation(self, setup_user_and_ledger: E2ETestHelper):
        """Balance aggregates correctly through multiple hierarchy levels."""
        helper = setup_user_and_ledger

        # Create 3-level hierarchy
        living = helper.create_account("Living Expenses", "EXPENSE")
        utilities = helper.create_account("Utilities", "EXPENSE", parent_id=living["id"])
        electricity = helper.create_account("Electricity", "EXPENSE", parent_id=utilities["id"])
        water = helper.create_account("Water", "EXPENSE", parent_id=utilities["id"])
        rent = helper.create_account("Rent", "EXPENSE", parent_id=living["id"])

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)

        # Create transactions to leaf accounts
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=electricity["id"],
            amount=100.0,
            transaction_type="EXPENSE",
        )
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=water["id"],
            amount=30.0,
            transaction_type="EXPENSE",
        )
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=rent["id"],
            amount=1500.0,
            transaction_type="EXPENSE",
        )

        # Verify each level
        elec_bal = helper.get_account(electricity["id"])
        water_bal = helper.get_account(water["id"])
        rent_bal = helper.get_account(rent["id"])
        util_bal = helper.get_account(utilities["id"])
        living_bal = helper.get_account(living["id"])

        assert Decimal(elec_bal["balance"]) == Decimal("100.00")
        assert Decimal(water_bal["balance"]) == Decimal("30.00")
        assert Decimal(rent_bal["balance"]) == Decimal("1500.00")
        assert Decimal(util_bal["balance"]) == Decimal("130.00")  # 100 + 30
        assert Decimal(living_bal["balance"]) == Decimal("1630.00")  # 130 + 1500

    def test_bal_008_income_increases_asset_balance(self, setup_user_and_ledger: E2ETestHelper):
        """Income transaction increases asset balance."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        initial_cash = Decimal(cash["balance"])

        salary = helper.create_account("Salary", "INCOME")

        # Create income transaction
        helper.create_transaction(
            from_account_id=salary["id"],
            to_account_id=cash["id"],
            amount=3000.0,
            transaction_type="INCOME",
        )

        # Cash should increase
        updated_cash = helper.get_account(cash["id"])
        assert Decimal(updated_cash["balance"]) == initial_cash + Decimal("3000.00")

    def test_bal_009_transfer_moves_balance(self, setup_user_and_ledger: E2ETestHelper):
        """Transfer moves balance between accounts."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        initial_cash = Decimal(cash["balance"])

        bank = helper.create_account("Bank", "ASSET")

        # Transfer from cash to bank
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=bank["id"],
            amount=500.0,
            transaction_type="TRANSFER",
        )

        updated_cash = helper.get_account(cash["id"])
        updated_bank = helper.get_account(bank["id"])

        assert Decimal(updated_cash["balance"]) == initial_cash - Decimal("500.00")
        assert Decimal(updated_bank["balance"]) == Decimal("500.00")

    def test_bal_010_zero_balance_new_account(self, setup_user_and_ledger: E2ETestHelper):
        """New accounts start with zero balance."""
        helper = setup_user_and_ledger

        account = helper.create_account("New Account", "EXPENSE")

        assert Decimal(account["balance"]) == Decimal("0.00")
