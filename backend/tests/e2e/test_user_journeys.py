"""E2E tests for Complete User Journeys (TC-JRN-xxx).

Tests end-to-end user flows through the entire system.
"""

import uuid
from decimal import Decimal

import pytest

from tests.e2e.conftest import E2ETestHelper


class TestUserJourneys:
    """TC-JRN: Complete User Journey tests."""

    def test_jrn_001_new_user_full_setup(self, e2e_helper: E2ETestHelper):
        """TC-JRN-001: New user complete setup journey."""
        # Step 1: Register new user
        user = e2e_helper.setup_user(f"journey-{uuid.uuid4()}@example.com")
        assert user["id"] is not None

        # Step 2: Create ledger with initial balance
        ledger = e2e_helper.create_ledger("Personal Budget", 5000.0)
        assert ledger["name"] == "Personal Budget"

        # Step 3: Create hierarchical expense accounts
        food = e2e_helper.create_account("Food", "EXPENSE")
        groceries = e2e_helper.create_account("Groceries", "EXPENSE", parent_id=food["id"])
        restaurants = e2e_helper.create_account("Restaurants", "EXPENSE", parent_id=food["id"])
        transportation = e2e_helper.create_account("Transportation", "EXPENSE")

        # Step 4: Create income account
        salary = e2e_helper.create_account("Salary", "INCOME")

        # Step 5: Get system Cash account
        accounts = e2e_helper.list_accounts()
        cash = e2e_helper.find_account_by_name("Cash", accounts)

        # Step 6: Record income transaction
        income_txn = e2e_helper.create_transaction(
            from_account_id=salary["id"],
            to_account_id=cash["id"],
            amount=3000.0,
            transaction_type="INCOME",
            description="Monthly salary",
            date="2024-01-01",
        )
        assert income_txn["transaction_type"] == "INCOME"

        # Step 7: Record expense transactions
        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=200.0,
            transaction_type="EXPENSE",
            description="Weekly groceries",
            date="2024-01-05",
        )

        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=restaurants["id"],
            amount=50.0,
            transaction_type="EXPENSE",
            description="Dinner out",
            date="2024-01-10",
        )

        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=transportation["id"],
            amount=100.0,
            transaction_type="EXPENSE",
            description="Gas",
            date="2024-01-12",
        )

        # Step 8: Verify final balances
        final_cash = e2e_helper.get_account(cash["id"])
        # 5000 (initial) + 3000 (income) - 200 - 50 - 100 = 7650
        assert Decimal(final_cash["balance"]) == Decimal("7650.00")

        # Step 9: Verify account tree with aggregated balances
        tree = e2e_helper.get_account_tree()
        food_node = None
        for node in tree:
            if node["name"] == "Food":
                food_node = node
                break

        assert food_node is not None
        # Food should aggregate: 200 + 50 = 250
        assert Decimal(food_node["balance"]) == Decimal("250.00")

        # Step 10: Verify transaction list
        # Note: Initial balance also creates a transaction (Equity -> Cash)
        txns = e2e_helper.list_transactions()
        assert len(txns["data"]) >= 4  # 4 user transactions + 1 initial balance

    def test_jrn_002_monthly_expense_tracking(self, e2e_helper: E2ETestHelper):
        """TC-JRN-002: Track and categorize monthly expenses."""
        e2e_helper.setup_user(f"monthly-{uuid.uuid4()}@example.com")
        e2e_helper.create_ledger("Monthly Tracking", 10000.0)

        # Create expense categories
        living = e2e_helper.create_account("Living Expenses", "EXPENSE")
        rent = e2e_helper.create_account("Rent", "EXPENSE", parent_id=living["id"])
        utilities = e2e_helper.create_account("Utilities", "EXPENSE", parent_id=living["id"])

        food = e2e_helper.create_account("Food", "EXPENSE")
        groceries = e2e_helper.create_account("Groceries", "EXPENSE", parent_id=food["id"])

        transport = e2e_helper.create_account("Transport", "EXPENSE")

        accounts = e2e_helper.list_accounts()
        cash = e2e_helper.find_account_by_name("Cash", accounts)

        # Record January expenses
        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=rent["id"],
            amount=1500.0,
            transaction_type="EXPENSE",
            description="January rent",
            date="2024-01-01",
        )
        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=utilities["id"],
            amount=150.0,
            transaction_type="EXPENSE",
            description="January utilities",
            date="2024-01-15",
        )
        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=400.0,
            transaction_type="EXPENSE",
            description="January groceries",
            date="2024-01-20",
        )
        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=transport["id"],
            amount=200.0,
            transaction_type="EXPENSE",
            description="January gas",
            date="2024-01-25",
        )

        # Record February expenses
        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=rent["id"],
            amount=1500.0,
            transaction_type="EXPENSE",
            description="February rent",
            date="2024-02-01",
        )

        # Filter January transactions
        jan_txns = e2e_helper.list_transactions(
            from_date="2024-01-01",
            to_date="2024-01-31",
        )
        assert len(jan_txns["data"]) == 4

        # Verify category totals
        tree = e2e_helper.get_account_tree()

        living_node = None
        food_node = None
        for node in tree:
            if node["name"] == "Living Expenses":
                living_node = node
            elif node["name"] == "Food":
                food_node = node

        # Living: 1500 + 150 + 1500 = 3150
        assert Decimal(living_node["balance"]) == Decimal("3150.00")
        # Food: 400
        assert Decimal(food_node["balance"]) == Decimal("400.00")

    def test_jrn_003_income_and_savings(self, e2e_helper: E2ETestHelper):
        """Track income and transfer to savings."""
        e2e_helper.setup_user(f"savings-{uuid.uuid4()}@example.com")
        e2e_helper.create_ledger("Income & Savings", 0.0)

        # Create accounts
        salary = e2e_helper.create_account("Salary", "INCOME")
        freelance = e2e_helper.create_account("Freelance", "INCOME")
        bank = e2e_helper.create_account("Bank Account", "ASSET")
        savings = e2e_helper.create_account("Savings Account", "ASSET")

        accounts = e2e_helper.list_accounts()
        cash = e2e_helper.find_account_by_name("Cash", accounts)

        # Receive salary
        e2e_helper.create_transaction(
            from_account_id=salary["id"],
            to_account_id=bank["id"],
            amount=5000.0,
            transaction_type="INCOME",
            description="Monthly salary",
        )

        # Receive freelance income
        e2e_helper.create_transaction(
            from_account_id=freelance["id"],
            to_account_id=bank["id"],
            amount=1000.0,
            transaction_type="INCOME",
            description="Freelance project",
        )

        # Transfer to savings
        e2e_helper.create_transaction(
            from_account_id=bank["id"],
            to_account_id=savings["id"],
            amount=2000.0,
            transaction_type="TRANSFER",
            description="Monthly savings",
        )

        # Verify balances
        bank_bal = e2e_helper.get_account(bank["id"])
        savings_bal = e2e_helper.get_account(savings["id"])

        assert Decimal(bank_bal["balance"]) == Decimal("4000.00")  # 5000 + 1000 - 2000
        assert Decimal(savings_bal["balance"]) == Decimal("2000.00")

    def test_jrn_004_full_accounting_cycle(self, e2e_helper: E2ETestHelper):
        """Complete accounting cycle: income, expenses, transfers."""
        e2e_helper.setup_user(f"cycle-{uuid.uuid4()}@example.com")
        e2e_helper.create_ledger("Full Cycle", 1000.0)

        # Set up accounts
        salary = e2e_helper.create_account("Salary", "INCOME")
        bank = e2e_helper.create_account("Bank", "ASSET")
        credit_card = e2e_helper.create_account("Credit Card", "LIABILITY")

        food = e2e_helper.create_account("Food", "EXPENSE")
        groceries = e2e_helper.create_account("Groceries", "EXPENSE", parent_id=food["id"])

        accounts = e2e_helper.list_accounts()
        cash = e2e_helper.find_account_by_name("Cash", accounts)

        # Receive income to bank
        e2e_helper.create_transaction(
            from_account_id=salary["id"],
            to_account_id=bank["id"],
            amount=5000.0,
            transaction_type="INCOME",
        )

        # Transfer from bank to cash
        e2e_helper.create_transaction(
            from_account_id=bank["id"],
            to_account_id=cash["id"],
            amount=500.0,
            transaction_type="TRANSFER",
        )

        # Pay expense with cash
        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=100.0,
            transaction_type="EXPENSE",
        )

        # Pay expense with credit card (liability increases)
        e2e_helper.create_transaction(
            from_account_id=credit_card["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
        )

        # Pay off credit card from bank
        e2e_helper.create_transaction(
            from_account_id=bank["id"],
            to_account_id=credit_card["id"],
            amount=50.0,
            transaction_type="TRANSFER",
        )

        # Verify final state
        final_cash = e2e_helper.get_account(cash["id"])
        final_bank = e2e_helper.get_account(bank["id"])
        final_cc = e2e_helper.get_account(credit_card["id"])
        final_groceries = e2e_helper.get_account(groceries["id"])

        # Cash: 1000 (initial) + 500 (transfer in) - 100 (expense) = 1400
        assert Decimal(final_cash["balance"]) == Decimal("1400.00")
        # Bank: 5000 (income) - 500 (to cash) - 50 (pay CC) = 4450
        assert Decimal(final_bank["balance"]) == Decimal("4450.00")
        # Credit card: -50 (expense) + 50 (payment) = 0
        assert Decimal(final_cc["balance"]) == Decimal("0.00")
        # Groceries: 100 + 50 = 150
        assert Decimal(final_groceries["balance"]) == Decimal("150.00")

    def test_jrn_005_edit_and_delete_journey(self, e2e_helper: E2ETestHelper):
        """Edit and delete transactions, verify balance corrections."""
        e2e_helper.setup_user(f"edit-{uuid.uuid4()}@example.com")
        e2e_helper.create_ledger("Edit Journey", 1000.0)

        groceries = e2e_helper.create_account("Groceries", "EXPENSE")

        accounts = e2e_helper.list_accounts()
        cash = e2e_helper.find_account_by_name("Cash", accounts)

        # Create transaction
        txn = e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
            description="Original groceries",
        )

        # Verify initial balance
        cash_after_create = e2e_helper.get_account(cash["id"])
        assert Decimal(cash_after_create["balance"]) == Decimal("950.00")

        # Edit transaction - increase amount
        e2e_helper.update_transaction(
            transaction_id=txn["id"],
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=80.0,
            transaction_type="EXPENSE",
            description="Updated groceries",
            date="2024-01-15",
        )

        cash_after_edit = e2e_helper.get_account(cash["id"])
        assert Decimal(cash_after_edit["balance"]) == Decimal("920.00")

        # Delete transaction
        e2e_helper.delete_transaction(txn["id"])

        cash_after_delete = e2e_helper.get_account(cash["id"])
        assert Decimal(cash_after_delete["balance"]) == Decimal("1000.00")

    def test_jrn_006_multi_ledger_user(self, e2e_helper: E2ETestHelper):
        """User manages multiple ledgers."""
        e2e_helper.setup_user(f"multi-{uuid.uuid4()}@example.com")

        # Create personal ledger
        personal = e2e_helper.create_ledger("Personal", 5000.0)
        personal_id = personal["id"]

        e2e_helper.create_account("Groceries", "EXPENSE")
        accounts = e2e_helper.list_accounts()
        cash = e2e_helper.find_account_by_name("Cash", accounts)
        groceries = e2e_helper.find_account_by_name("Groceries", accounts)

        e2e_helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=100.0,
            transaction_type="EXPENSE",
        )

        # Create business ledger
        business = e2e_helper.create_ledger("Business", 10000.0)
        business_id = business["id"]

        e2e_helper.create_account("Office Supplies", "EXPENSE")
        biz_accounts = e2e_helper.list_accounts()
        biz_cash = e2e_helper.find_account_by_name("Cash", biz_accounts)
        supplies = e2e_helper.find_account_by_name("Office Supplies", biz_accounts)

        e2e_helper.create_transaction(
            from_account_id=biz_cash["id"],
            to_account_id=supplies["id"],
            amount=500.0,
            transaction_type="EXPENSE",
        )

        # Verify ledger list
        ledgers = e2e_helper.list_ledgers()
        assert len(ledgers) == 2

        # Verify isolation - each ledger has correct balances
        e2e_helper.ledger_id = personal_id
        personal_accounts = e2e_helper.list_accounts()
        personal_cash = e2e_helper.find_account_by_name("Cash", personal_accounts)
        assert Decimal(personal_cash["balance"]) == Decimal("4900.00")

        e2e_helper.ledger_id = business_id
        biz_accounts = e2e_helper.list_accounts()
        biz_cash = e2e_helper.find_account_by_name("Cash", biz_accounts)
        assert Decimal(biz_cash["balance"]) == Decimal("9500.00")
