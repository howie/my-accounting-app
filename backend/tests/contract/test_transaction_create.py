"""Contract tests for POST /api/v1/ledgers/{id}/transactions endpoint.

Tests the API contract as defined in contracts/transactions.yaml.
These tests verify the HTTP API behavior, not the service layer.
"""

import uuid

import pytest
from fastapi.testclient import TestClient


class TestCreateTransactionEndpoint:
    """Contract tests for POST /api/v1/ledgers/{ledgerId}/transactions."""

    @pytest.fixture
    def ledger_id(self, client: TestClient) -> str:
        """Create a test ledger via API and return its ID."""
        response = client.post(
            "/api/v1/ledgers",
            json={"name": "Test Ledger", "initial_balance": "5000.00"},
        )
        return response.json()["id"]

    @pytest.fixture
    def cash_account_id(self, client: TestClient, ledger_id: str) -> str:
        """Get the Cash account ID (created automatically with ledger)."""
        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")
        accounts = response.json()["data"]
        return next(a["id"] for a in accounts if a["name"] == "Cash")

    @pytest.fixture
    def expense_account_id(self, client: TestClient, ledger_id: str) -> str:
        """Create an expense account via API and return its ID."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Food", "type": "EXPENSE"},
        )
        return response.json()["id"]

    @pytest.fixture
    def income_account_id(self, client: TestClient, ledger_id: str) -> str:
        """Create an income account via API and return its ID."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Salary", "type": "INCOME"},
        )
        return response.json()["id"]

    @pytest.fixture
    def bank_account_id(self, client: TestClient, ledger_id: str) -> str:
        """Create a bank asset account via API and return its ID."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Bank", "type": "ASSET"},
        )
        return response.json()["id"]

    # --- Success Cases (201 Created) ---

    def test_create_expense_transaction_returns_201(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """POST /api/v1/ledgers/{id}/transactions returns 201 for valid expense."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "午餐 - 麥當勞",
                "amount": 150.00,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
            },
        )

        assert response.status_code == 201

    def test_create_transaction_returns_transaction_with_id(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """Created transaction response includes valid UUID id."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Test expense",
                "amount": 50.00,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
            },
        )

        data = response.json()
        assert "id" in data
        # Verify it's a valid UUID
        uuid.UUID(data["id"])

    def test_create_transaction_returns_all_fields(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """Created transaction response includes all expected fields."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Full fields test",
                "amount": 100.00,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
                "notes": "與同事聚餐",
                "amount_expression": "50+50",
            },
        )

        data = response.json()
        assert data["date"] == "2026-01-09"
        assert data["description"] == "Full fields test"
        assert float(data["amount"]) == 100.00
        assert data["from_account_id"] == cash_account_id
        assert data["to_account_id"] == expense_account_id
        assert data["transaction_type"] == "EXPENSE"
        assert data["notes"] == "與同事聚餐"
        assert data["amount_expression"] == "50+50"
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_expense_with_notes(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """Creating expense with notes stores and returns notes correctly."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Lunch",
                "amount": 150.00,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
                "notes": "Business meeting at downtown restaurant",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["notes"] == "Business meeting at downtown restaurant"

    def test_create_expense_with_amount_expression(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """Creating expense with amount_expression stores it for audit trail."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Split expense",
                "amount": 250.00,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
                "amount_expression": "1000/4",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["amount_expression"] == "1000/4"
        assert float(data["amount"]) == 250.00

    def test_create_income_transaction(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        income_account_id: str,
    ) -> None:
        """POST creates income transaction (from Income to Asset)."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Monthly salary",
                "amount": 3000.00,
                "from_account_id": income_account_id,
                "to_account_id": cash_account_id,
                "transaction_type": "INCOME",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "INCOME"

    def test_create_transfer_transaction(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        bank_account_id: str,
    ) -> None:
        """POST creates transfer transaction (from Asset to Asset)."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Transfer to savings",
                "amount": 500.00,
                "from_account_id": cash_account_id,
                "to_account_id": bank_account_id,
                "transaction_type": "TRANSFER",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "TRANSFER"

    # --- Validation Error Cases (400 Bad Request) ---

    def test_create_transaction_same_account_returns_400(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
    ) -> None:
        """POST returns 400 when from and to accounts are the same."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Invalid same account",
                "amount": 50.00,
                "from_account_id": cash_account_id,
                "to_account_id": cash_account_id,
                "transaction_type": "TRANSFER",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "different" in data["detail"].lower()

    def test_create_expense_invalid_from_account_type_returns_400(
        self,
        client: TestClient,
        ledger_id: str,
        income_account_id: str,
        expense_account_id: str,
    ) -> None:
        """POST returns 400 for EXPENSE with Income as from_account."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Invalid expense from Income",
                "amount": 50.00,
                "from_account_id": income_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
            },
        )

        assert response.status_code == 400

    def test_create_income_invalid_to_account_type_returns_400(
        self,
        client: TestClient,
        ledger_id: str,
        income_account_id: str,
        expense_account_id: str,
    ) -> None:
        """POST returns 400 for INCOME with Expense as to_account."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Invalid income to Expense",
                "amount": 50.00,
                "from_account_id": income_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "INCOME",
            },
        )

        assert response.status_code == 400

    def test_create_transaction_missing_description_returns_422(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """POST returns 422 when description is missing."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "amount": 50.00,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
            },
        )

        assert response.status_code == 422

    def test_create_transaction_empty_description_returns_422(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """POST returns 422 when description is empty string."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "",
                "amount": 50.00,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
            },
        )

        assert response.status_code == 422

    def test_create_transaction_whitespace_description_returns_422(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """POST returns 422 when description is whitespace only."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "   ",
                "amount": 50.00,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
            },
        )

        assert response.status_code == 422

    def test_create_transaction_negative_amount_returns_422(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """POST returns 422 when amount is negative."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Negative amount",
                "amount": -50.00,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
            },
        )

        assert response.status_code == 422

    def test_create_transaction_zero_amount_returns_422(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """POST returns 422 when amount is zero."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Zero amount",
                "amount": 0,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
            },
        )

        assert response.status_code == 422

    # --- Not Found Cases (404) ---

    def test_create_transaction_nonexistent_ledger_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """POST returns 404 for non-existent ledger."""
        fake_ledger_id = uuid.uuid4()
        fake_account_id = uuid.uuid4()
        response = client.post(
            f"/api/v1/ledgers/{fake_ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Test",
                "amount": 50.00,
                "from_account_id": str(fake_account_id),
                "to_account_id": str(fake_account_id),
                "transaction_type": "EXPENSE",
            },
        )

        assert response.status_code == 404

    def test_create_transaction_nonexistent_from_account_returns_400(
        self,
        client: TestClient,
        ledger_id: str,
        expense_account_id: str,
    ) -> None:
        """POST returns 400 for non-existent from_account."""
        fake_account_id = str(uuid.uuid4())
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Test",
                "amount": 50.00,
                "from_account_id": fake_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
            },
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_create_transaction_nonexistent_to_account_returns_400(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
    ) -> None:
        """POST returns 400 for non-existent to_account."""
        fake_account_id = str(uuid.uuid4())
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Test",
                "amount": 50.00,
                "from_account_id": cash_account_id,
                "to_account_id": fake_account_id,
                "transaction_type": "EXPENSE",
            },
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    # --- Notes Field Validation ---

    def test_create_transaction_without_notes_has_null(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """Transaction without notes field has null notes in response."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "No notes",
                "amount": 50.00,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["notes"] is None

    def test_create_transaction_notes_max_length_500(
        self,
        client: TestClient,
        ledger_id: str,
        cash_account_id: str,
        expense_account_id: str,
    ) -> None:
        """Transaction accepts notes up to 500 characters."""
        long_notes = "A" * 500
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/transactions",
            json={
                "date": "2026-01-09",
                "description": "Long notes test",
                "amount": 50.00,
                "from_account_id": cash_account_id,
                "to_account_id": expense_account_id,
                "transaction_type": "EXPENSE",
                "notes": long_notes,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["notes"]) == 500
