"""E2E tests for Transaction Management (TC-TXN-xxx).

Tests transaction CRUD, validations, and filtering.
"""

import uuid
from decimal import Decimal

from fastapi.testclient import TestClient

from tests.e2e.conftest import E2ETestHelper


class TestTransactions:
    """TC-TXN: Transaction Management tests."""

    def test_txn_001_create_expense_transaction(self, setup_user_and_ledger: E2ETestHelper):
        """TC-TXN-001: Create EXPENSE transaction."""
        helper = setup_user_and_ledger

        # Get Cash and create Groceries
        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        groceries = helper.create_account("Groceries", "EXPENSE")

        initial_cash_balance = Decimal(cash["balance"])

        # Create expense
        txn = helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
            description="Weekly groceries",
            date="2024-01-15",
        )

        assert txn["amount"] == "50.00"
        assert txn["transaction_type"] == "EXPENSE"
        assert txn["description"] == "Weekly groceries"

        # Verify balances updated
        updated_cash = helper.get_account(cash["id"])
        updated_groceries = helper.get_account(groceries["id"])

        assert Decimal(updated_cash["balance"]) == initial_cash_balance - Decimal("50.00")
        assert Decimal(updated_groceries["balance"]) == Decimal("50.00")

    def test_txn_002_create_income_transaction(self, setup_user_and_ledger: E2ETestHelper):
        """TC-TXN-002: Create INCOME transaction."""
        helper = setup_user_and_ledger

        # Create Salary (INCOME) and Bank (ASSET)
        salary = helper.create_account("Salary", "INCOME")
        bank = helper.create_account("Bank Account", "ASSET")

        # Create income
        txn = helper.create_transaction(
            from_account_id=salary["id"],
            to_account_id=bank["id"],
            amount=3000.0,
            transaction_type="INCOME",
            description="Monthly salary",
        )

        assert txn["transaction_type"] == "INCOME"

        # Verify bank balance increased
        updated_bank = helper.get_account(bank["id"])
        assert Decimal(updated_bank["balance"]) == Decimal("3000.00")

    def test_txn_003_create_transfer_transaction(self, setup_user_and_ledger: E2ETestHelper):
        """TC-TXN-003: Create TRANSFER transaction."""
        helper = setup_user_and_ledger

        # Get Cash and create Bank
        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        bank = helper.create_account("Bank Account", "ASSET")

        initial_cash = Decimal(cash["balance"])

        # Transfer from Cash to Bank
        txn = helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=bank["id"],
            amount=200.0,
            transaction_type="TRANSFER",
            description="Deposit to bank",
        )

        assert txn["transaction_type"] == "TRANSFER"

        # Verify balances
        updated_cash = helper.get_account(cash["id"])
        updated_bank = helper.get_account(bank["id"])

        assert Decimal(updated_cash["balance"]) == initial_cash - Decimal("200.00")
        assert Decimal(updated_bank["balance"]) == Decimal("200.00")

    def test_txn_004_invalid_expense_from_account(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """TC-TXN-004: EXPENSE from_account must be Asset/Liability."""
        helper = setup_user_and_ledger

        # Create INCOME and EXPENSE accounts
        salary = helper.create_account("Salary", "INCOME")
        groceries = helper.create_account("Groceries", "EXPENSE")

        # Try EXPENSE from INCOME account - should fail
        response = client.post(
            f"/api/v1/ledgers/{helper.ledger_id}/transactions",
            json={
                "from_account_id": salary["id"],
                "to_account_id": groceries["id"],
                "amount": 50.0,
                "transaction_type": "EXPENSE",
                "description": "Invalid",
                "date": "2024-01-15",
            },
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 400
        assert (
            "asset" in response.json()["detail"].lower()
            or "liability" in response.json()["detail"].lower()
        )

    def test_txn_005_same_account_transaction_rejected(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """TC-TXN-005: Cannot create transaction with same from and to account."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)

        response = client.post(
            f"/api/v1/ledgers/{helper.ledger_id}/transactions",
            json={
                "from_account_id": cash["id"],
                "to_account_id": cash["id"],
                "amount": 50.0,
                "transaction_type": "TRANSFER",
                "description": "Invalid",
                "date": "2024-01-15",
            },
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 400
        # Error message says accounts must be "different"
        detail = response.json()["detail"].lower()
        assert "same" in detail or "different" in detail

    def test_txn_006_update_transaction(self, setup_user_and_ledger: E2ETestHelper):
        """TC-TXN-006: Update transaction amount."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        groceries = helper.create_account("Groceries", "EXPENSE")

        initial_cash = Decimal(cash["balance"])

        # Create transaction
        txn = helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
        )

        # Update to higher amount
        updated = helper.update_transaction(
            transaction_id=txn["id"],
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=75.0,
            transaction_type="EXPENSE",
            description="Updated groceries",
            date="2024-01-15",
        )

        assert Decimal(updated["amount"]) == Decimal("75.00")

        # Verify balances reflect update
        final_cash = helper.get_account(cash["id"])
        final_groceries = helper.get_account(groceries["id"])

        assert Decimal(final_cash["balance"]) == initial_cash - Decimal("75.00")
        assert Decimal(final_groceries["balance"]) == Decimal("75.00")

    def test_txn_007_delete_transaction(self, setup_user_and_ledger: E2ETestHelper):
        """TC-TXN-007: Delete transaction restores balances."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        groceries = helper.create_account("Groceries", "EXPENSE")

        initial_cash = Decimal(cash["balance"])

        # Create and then delete transaction
        txn = helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
        )

        helper.delete_transaction(txn["id"])

        # Balances should be restored
        final_cash = helper.get_account(cash["id"])
        final_groceries = helper.get_account(groceries["id"])

        assert Decimal(final_cash["balance"]) == initial_cash
        assert Decimal(final_groceries["balance"]) == Decimal("0.00")

    def test_txn_008_transaction_list_pagination(self, setup_user_and_ledger: E2ETestHelper):
        """TC-TXN-008: Transaction list supports pagination."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        groceries = helper.create_account("Groceries", "EXPENSE")

        # Create 10 transactions
        for i in range(10):
            helper.create_transaction(
                from_account_id=cash["id"],
                to_account_id=groceries["id"],
                amount=10.0,
                transaction_type="EXPENSE",
                description=f"Transaction {i + 1}",
                date=f"2024-01-{15 + i:02d}",
            )

        # Get first page
        result = helper.list_transactions()

        assert "data" in result
        assert "has_more" in result
        assert len(result["data"]) > 0

    def test_txn_009_search_transactions(self, setup_user_and_ledger: E2ETestHelper):
        """TC-TXN-009: Search transactions by description."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        groceries = helper.create_account("Groceries", "EXPENSE")

        # Create transactions with different descriptions
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
            description="Weekly grocery shopping",
        )
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=30.0,
            transaction_type="EXPENSE",
            description="Coffee and snacks",
        )

        # Search for "grocery"
        result = helper.list_transactions(search="grocery")

        assert len(result["data"]) == 1
        assert "grocery" in result["data"][0]["description"].lower()

    def test_txn_010_filter_by_date_range(self, setup_user_and_ledger: E2ETestHelper):
        """TC-TXN-010: Filter transactions by date range."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        groceries = helper.create_account("Groceries", "EXPENSE")

        # Create transactions on different dates
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
            date="2024-01-10",
        )
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=60.0,
            transaction_type="EXPENSE",
            date="2024-01-20",
        )
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=70.0,
            transaction_type="EXPENSE",
            date="2024-02-05",
        )

        # Filter January only
        result = helper.list_transactions(from_date="2024-01-01", to_date="2024-01-31")

        assert len(result["data"]) == 2

    def test_txn_011_filter_by_account(self, setup_user_and_ledger: E2ETestHelper):
        """TC-TXN-011: Filter transactions by account."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        groceries = helper.create_account("Groceries", "EXPENSE")
        transport = helper.create_account("Transport", "EXPENSE")

        # Create transactions to different accounts
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
        )
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=transport["id"],
            amount=30.0,
            transaction_type="EXPENSE",
        )

        # Filter by Groceries account
        result = helper.list_transactions(account_id=groceries["id"])

        assert len(result["data"]) == 1
        to_account = result["data"][0]["to_account"]
        assert to_account["name"] == "Groceries"

    def test_txn_012_filter_by_type(self, setup_user_and_ledger: E2ETestHelper):
        """TC-TXN-012: Filter transactions by type."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        groceries = helper.create_account("Groceries", "EXPENSE")
        salary = helper.create_account("Salary", "INCOME")

        # Create different transaction types
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
        )
        helper.create_transaction(
            from_account_id=salary["id"],
            to_account_id=cash["id"],
            amount=3000.0,
            transaction_type="INCOME",
        )

        # Filter by EXPENSE
        result = helper.list_transactions(transaction_type="EXPENSE")

        assert len(result["data"]) == 1
        assert result["data"][0]["transaction_type"] == "EXPENSE"

    def test_txn_013_get_single_transaction(self, setup_user_and_ledger: E2ETestHelper):
        """Get single transaction by ID."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        groceries = helper.create_account("Groceries", "EXPENSE")

        created = helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=50.0,
            transaction_type="EXPENSE",
            description="Test transaction",
        )

        # Fetch by ID
        txn = helper.get_transaction(created["id"])

        assert txn["id"] == created["id"]
        assert txn["description"] == "Test transaction"
        assert txn["from_account"]["name"] == "Cash"
        assert txn["to_account"]["name"] == "Groceries"

    def test_txn_014_transaction_not_found(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """Accessing non-existent transaction returns 404."""
        helper = setup_user_and_ledger

        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/ledgers/{helper.ledger_id}/transactions/{fake_id}",
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 404

    def test_txn_015_invalid_income_accounts(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """INCOME from_account must be INCOME type."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        bank = helper.create_account("Bank", "ASSET")

        # Try INCOME from ASSET - should fail
        response = client.post(
            f"/api/v1/ledgers/{helper.ledger_id}/transactions",
            json={
                "from_account_id": cash["id"],
                "to_account_id": bank["id"],
                "amount": 100.0,
                "transaction_type": "INCOME",
                "description": "Invalid",
                "date": "2024-01-15",
            },
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 400

    def test_txn_016_invalid_transfer_accounts(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """TRANSFER accounts must be Asset/Liability."""
        helper = setup_user_and_ledger

        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)
        groceries = helper.create_account("Groceries", "EXPENSE")

        # Try TRANSFER to EXPENSE - should fail
        response = client.post(
            f"/api/v1/ledgers/{helper.ledger_id}/transactions",
            json={
                "from_account_id": cash["id"],
                "to_account_id": groceries["id"],
                "amount": 100.0,
                "transaction_type": "TRANSFER",
                "description": "Invalid",
                "date": "2024-01-15",
            },
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 400
