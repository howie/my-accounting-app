"""Contract tests for Template API endpoints.

Tests the REST API contract for transaction templates.
"""

import uuid
from datetime import date

from fastapi.testclient import TestClient


class TestTemplateEndpointsContract:
    """Contract tests for /api/v1/ledgers/{ledger_id}/templates endpoints."""

    def _create_ledger(self, client: TestClient) -> str:
        """Helper to create a ledger and return its ID."""
        response = client.post(
            "/api/v1/ledgers",
            json={"name": "Test Ledger", "initial_balance": "1000.00"},
        )
        return response.json()["id"]

    def _create_expense_account(
        self, client: TestClient, ledger_id: str, name: str = "Food"
    ) -> str:
        """Helper to create an expense account and return its ID."""
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": name, "type": "EXPENSE"},
        )
        return response.json()["id"]

    def _get_cash_account_id(self, client: TestClient, ledger_id: str) -> str:
        """Helper to get the Cash account ID from a ledger."""
        response = client.get(f"/api/v1/ledgers/{ledger_id}/accounts")
        accounts = response.json()["data"]
        cash = next(a for a in accounts if a["name"] == "Cash")
        return cash["id"]

    def _create_template(
        self,
        client: TestClient,
        ledger_id: str,
        name: str = "Test Template",
        amount: str = "50.00",
        expense_account_name: str | None = None,
    ) -> dict:
        """Helper to create a template and return its data."""
        cash_id = self._get_cash_account_id(client, ledger_id)
        # Use unique expense account name to avoid duplicates
        account_name = expense_account_name or f"Expense-{name}"
        expense_id = self._create_expense_account(client, ledger_id, account_name)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates",
            json={
                "name": name,
                "transaction_type": "EXPENSE",
                "from_account_id": cash_id,
                "to_account_id": expense_id,
                "amount": amount,
                "description": f"Description for {name}",
            },
        )
        return response.json()

    # --- GET /api/v1/ledgers/{ledger_id}/templates ---

    def test_list_templates_returns_200(self, client: TestClient) -> None:
        """GET /templates returns 200 OK."""
        ledger_id = self._create_ledger(client)

        response = client.get(f"/api/v1/ledgers/{ledger_id}/templates")

        assert response.status_code == 200

    def test_list_templates_returns_data_and_total(self, client: TestClient) -> None:
        """GET /templates returns data list and total count."""
        ledger_id = self._create_ledger(client)

        response = client.get(f"/api/v1/ledgers/{ledger_id}/templates")

        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    def test_list_templates_empty_for_new_ledger(self, client: TestClient) -> None:
        """GET /templates returns empty list for ledger with no templates."""
        ledger_id = self._create_ledger(client)

        response = client.get(f"/api/v1/ledgers/{ledger_id}/templates")

        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    def test_list_templates_returns_created_templates(self, client: TestClient) -> None:
        """GET /templates returns templates after creation."""
        ledger_id = self._create_ledger(client)
        self._create_template(client, ledger_id, "Template 1")

        response = client.get(f"/api/v1/ledgers/{ledger_id}/templates")

        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Template 1"

    def test_list_templates_item_has_required_fields(self, client: TestClient) -> None:
        """GET /templates items have all required fields."""
        ledger_id = self._create_ledger(client)
        self._create_template(client, ledger_id)

        response = client.get(f"/api/v1/ledgers/{ledger_id}/templates")

        template = response.json()["data"][0]
        assert "id" in template
        assert "name" in template
        assert "transaction_type" in template
        assert "from_account_id" in template
        assert "to_account_id" in template
        assert "amount" in template
        assert "description" in template
        assert "sort_order" in template

    def test_list_templates_returns_404_for_nonexistent_ledger(
        self, client: TestClient
    ) -> None:
        """GET /templates returns 404 for non-existent ledger."""
        fake_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/ledgers/{fake_id}/templates")

        assert response.status_code == 404

    # --- POST /api/v1/ledgers/{ledger_id}/templates ---

    def test_create_template_returns_201(self, client: TestClient) -> None:
        """POST /templates returns 201 Created on success."""
        ledger_id = self._create_ledger(client)
        cash_id = self._get_cash_account_id(client, ledger_id)
        expense_id = self._create_expense_account(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates",
            json={
                "name": "Lunch",
                "transaction_type": "EXPENSE",
                "from_account_id": cash_id,
                "to_account_id": expense_id,
                "amount": "25.00",
                "description": "Daily lunch expense",
            },
        )

        assert response.status_code == 201

    def test_create_template_returns_template_data(self, client: TestClient) -> None:
        """POST /templates returns the created template data."""
        ledger_id = self._create_ledger(client)
        cash_id = self._get_cash_account_id(client, ledger_id)
        expense_id = self._create_expense_account(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates",
            json={
                "name": "Monthly Rent",
                "transaction_type": "EXPENSE",
                "from_account_id": cash_id,
                "to_account_id": expense_id,
                "amount": "1500.00",
                "description": "Monthly rent payment",
            },
        )

        data = response.json()
        assert "id" in data
        assert data["name"] == "Monthly Rent"
        assert data["amount"] == "1500.00"
        assert data["description"] == "Monthly rent payment"
        assert data["transaction_type"] == "EXPENSE"

    def test_create_template_returns_uuid_id(self, client: TestClient) -> None:
        """POST /templates returns a valid UUID as id."""
        ledger_id = self._create_ledger(client)
        template = self._create_template(client, ledger_id)

        uuid.UUID(template["id"])  # Should not raise

    def test_create_template_returns_timestamps(self, client: TestClient) -> None:
        """POST /templates returns created_at and updated_at timestamps."""
        ledger_id = self._create_ledger(client)
        template = self._create_template(client, ledger_id)

        assert "created_at" in template
        assert "updated_at" in template
        assert template["created_at"] is not None
        assert template["updated_at"] is not None

    def test_create_template_empty_name_returns_422(self, client: TestClient) -> None:
        """POST /templates returns 422 for empty name."""
        ledger_id = self._create_ledger(client)
        cash_id = self._get_cash_account_id(client, ledger_id)
        expense_id = self._create_expense_account(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates",
            json={
                "name": "",
                "transaction_type": "EXPENSE",
                "from_account_id": cash_id,
                "to_account_id": expense_id,
                "amount": "25.00",
                "description": "Test",
            },
        )

        assert response.status_code == 422

    def test_create_template_duplicate_name_returns_422(self, client: TestClient) -> None:
        """POST /templates returns 422 for duplicate name in same ledger."""
        ledger_id = self._create_ledger(client)
        self._create_template(client, ledger_id, "Duplicate")

        cash_id = self._get_cash_account_id(client, ledger_id)
        # Create another expense account for second template
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Entertainment", "type": "EXPENSE"},
        )
        expense_id = response.json()["id"]

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates",
            json={
                "name": "Duplicate",
                "transaction_type": "EXPENSE",
                "from_account_id": cash_id,
                "to_account_id": expense_id,
                "amount": "100.00",
                "description": "Another template",
            },
        )

        assert response.status_code == 422

    def test_create_template_same_accounts_returns_422(self, client: TestClient) -> None:
        """POST /templates returns 422 when from and to accounts are the same."""
        ledger_id = self._create_ledger(client)
        cash_id = self._get_cash_account_id(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates",
            json={
                "name": "Invalid Transfer",
                "transaction_type": "TRANSFER",
                "from_account_id": cash_id,
                "to_account_id": cash_id,  # Same account
                "amount": "100.00",
                "description": "Invalid",
            },
        )

        assert response.status_code == 422

    def test_create_template_invalid_account_returns_422(self, client: TestClient) -> None:
        """POST /templates returns 422 for non-existent account."""
        ledger_id = self._create_ledger(client)
        cash_id = self._get_cash_account_id(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates",
            json={
                "name": "Invalid",
                "transaction_type": "EXPENSE",
                "from_account_id": cash_id,
                "to_account_id": str(uuid.uuid4()),  # Non-existent
                "amount": "50.00",
                "description": "Invalid account",
            },
        )

        assert response.status_code == 422

    def test_create_template_negative_amount_returns_422(self, client: TestClient) -> None:
        """POST /templates returns 422 for negative amount."""
        ledger_id = self._create_ledger(client)
        cash_id = self._get_cash_account_id(client, ledger_id)
        expense_id = self._create_expense_account(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates",
            json={
                "name": "Negative",
                "transaction_type": "EXPENSE",
                "from_account_id": cash_id,
                "to_account_id": expense_id,
                "amount": "-50.00",
                "description": "Negative amount",
            },
        )

        assert response.status_code == 422

    # --- GET /api/v1/ledgers/{ledger_id}/templates/{template_id} ---

    def test_get_template_returns_200(self, client: TestClient) -> None:
        """GET /templates/{id} returns 200 OK for existing template."""
        ledger_id = self._create_ledger(client)
        template = self._create_template(client, ledger_id)

        response = client.get(
            f"/api/v1/ledgers/{ledger_id}/templates/{template['id']}"
        )

        assert response.status_code == 200

    def test_get_template_returns_template_data(self, client: TestClient) -> None:
        """GET /templates/{id} returns the template data."""
        ledger_id = self._create_ledger(client)
        created = self._create_template(client, ledger_id, "Find Me")

        response = client.get(
            f"/api/v1/ledgers/{ledger_id}/templates/{created['id']}"
        )

        data = response.json()
        assert data["id"] == created["id"]
        assert data["name"] == "Find Me"

    def test_get_template_returns_full_details(self, client: TestClient) -> None:
        """GET /templates/{id} returns all template fields."""
        ledger_id = self._create_ledger(client)
        created = self._create_template(client, ledger_id)

        response = client.get(
            f"/api/v1/ledgers/{ledger_id}/templates/{created['id']}"
        )

        data = response.json()
        assert "id" in data
        assert "ledger_id" in data
        assert "name" in data
        assert "transaction_type" in data
        assert "from_account_id" in data
        assert "to_account_id" in data
        assert "amount" in data
        assert "description" in data
        assert "sort_order" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_template_nonexistent_returns_404(self, client: TestClient) -> None:
        """GET /templates/{id} returns 404 for non-existent template."""
        ledger_id = self._create_ledger(client)
        fake_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/ledgers/{ledger_id}/templates/{fake_id}")

        assert response.status_code == 404

    def test_get_template_other_ledger_returns_404(self, client: TestClient) -> None:
        """GET /templates/{id} returns 404 if template belongs to different ledger."""
        ledger_id = self._create_ledger(client)
        created = self._create_template(client, ledger_id)

        other_ledger_id = self._create_ledger(client)

        response = client.get(
            f"/api/v1/ledgers/{other_ledger_id}/templates/{created['id']}"
        )

        assert response.status_code == 404

    # --- PATCH /api/v1/ledgers/{ledger_id}/templates/{template_id} ---

    def test_update_template_returns_200(self, client: TestClient) -> None:
        """PATCH /templates/{id} returns 200 OK on success."""
        ledger_id = self._create_ledger(client)
        created = self._create_template(client, ledger_id)

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/templates/{created['id']}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200

    def test_update_template_changes_fields(self, client: TestClient) -> None:
        """PATCH /templates/{id} updates the specified fields."""
        ledger_id = self._create_ledger(client)
        created = self._create_template(client, ledger_id)

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/templates/{created['id']}",
            json={"name": "New Name", "amount": "99.00"},
        )

        data = response.json()
        assert data["name"] == "New Name"
        assert data["amount"] == "99.00"

    def test_update_template_partial_update(self, client: TestClient) -> None:
        """PATCH /templates/{id} only updates specified fields."""
        ledger_id = self._create_ledger(client)
        created = self._create_template(client, ledger_id, amount="50.00")

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/templates/{created['id']}",
            json={"description": "Updated description"},
        )

        data = response.json()
        assert data["name"] == created["name"]  # Unchanged
        assert data["amount"] == "50.00"  # Unchanged
        assert data["description"] == "Updated description"

    def test_update_template_nonexistent_returns_404(self, client: TestClient) -> None:
        """PATCH /templates/{id} returns 404 for non-existent template."""
        ledger_id = self._create_ledger(client)
        fake_id = str(uuid.uuid4())

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/templates/{fake_id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 404

    def test_update_template_duplicate_name_returns_422(self, client: TestClient) -> None:
        """PATCH /templates/{id} returns 422 for duplicate name."""
        ledger_id = self._create_ledger(client)
        self._create_template(client, ledger_id, "Existing")

        # Need to create second expense account for second template
        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/accounts",
            json={"name": "Transport", "type": "EXPENSE"},
        )
        expense_id = response.json()["id"]
        cash_id = self._get_cash_account_id(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates",
            json={
                "name": "To Update",
                "transaction_type": "EXPENSE",
                "from_account_id": cash_id,
                "to_account_id": expense_id,
                "amount": "75.00",
                "description": "Will be updated",
            },
        )
        to_update = response.json()

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/templates/{to_update['id']}",
            json={"name": "Existing"},
        )

        assert response.status_code == 422

    # --- DELETE /api/v1/ledgers/{ledger_id}/templates/{template_id} ---

    def test_delete_template_returns_204(self, client: TestClient) -> None:
        """DELETE /templates/{id} returns 204 No Content on success."""
        ledger_id = self._create_ledger(client)
        created = self._create_template(client, ledger_id)

        response = client.delete(
            f"/api/v1/ledgers/{ledger_id}/templates/{created['id']}"
        )

        assert response.status_code == 204

    def test_delete_template_removes_from_list(self, client: TestClient) -> None:
        """DELETE /templates/{id} removes the template from GET list."""
        ledger_id = self._create_ledger(client)
        created = self._create_template(client, ledger_id)

        client.delete(f"/api/v1/ledgers/{ledger_id}/templates/{created['id']}")

        response = client.get(f"/api/v1/ledgers/{ledger_id}/templates")
        data = response.json()
        assert len(data["data"]) == 0

    def test_delete_template_makes_get_return_404(self, client: TestClient) -> None:
        """DELETE /templates/{id} makes subsequent GET return 404."""
        ledger_id = self._create_ledger(client)
        created = self._create_template(client, ledger_id)

        client.delete(f"/api/v1/ledgers/{ledger_id}/templates/{created['id']}")

        response = client.get(
            f"/api/v1/ledgers/{ledger_id}/templates/{created['id']}"
        )
        assert response.status_code == 404

    def test_delete_template_nonexistent_returns_404(self, client: TestClient) -> None:
        """DELETE /templates/{id} returns 404 for non-existent template."""
        ledger_id = self._create_ledger(client)
        fake_id = str(uuid.uuid4())

        response = client.delete(f"/api/v1/ledgers/{ledger_id}/templates/{fake_id}")

        assert response.status_code == 404

    # --- PATCH /api/v1/ledgers/{ledger_id}/templates/reorder ---

    def test_reorder_templates_returns_200(self, client: TestClient) -> None:
        """PATCH /templates/reorder returns 200 OK on success."""
        ledger_id = self._create_ledger(client)
        t1 = self._create_template(client, ledger_id, "Template 1")
        t2 = self._create_template(client, ledger_id, "Template 2")

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/templates/reorder",
            json={"template_ids": [t2["id"], t1["id"]]},
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"

    def test_reorder_templates_changes_order(self, client: TestClient) -> None:
        """PATCH /templates/reorder changes the order of templates."""
        ledger_id = self._create_ledger(client)
        t1 = self._create_template(client, ledger_id, "Template 1")
        t2 = self._create_template(client, ledger_id, "Template 2")

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/templates/reorder",
            json={"template_ids": [t2["id"], t1["id"]]},
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
        data = response.json()
        assert data["data"][0]["id"] == t2["id"]
        assert data["data"][1]["id"] == t1["id"]

    def test_reorder_templates_mismatched_ids_returns_422(
        self, client: TestClient
    ) -> None:
        """PATCH /templates/reorder returns 422 if IDs don't match."""
        ledger_id = self._create_ledger(client)
        self._create_template(client, ledger_id)

        response = client.patch(
            f"/api/v1/ledgers/{ledger_id}/templates/reorder",
            json={"template_ids": [str(uuid.uuid4())]},
        )

        assert response.status_code == 422

    # --- POST /api/v1/ledgers/{ledger_id}/templates/{template_id}/apply ---

    def test_apply_template_returns_201(self, client: TestClient) -> None:
        """POST /templates/{id}/apply returns 201 Created."""
        ledger_id = self._create_ledger(client)
        template = self._create_template(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates/{template['id']}/apply"
        )

        assert response.status_code == 201

    def test_apply_template_creates_transaction(self, client: TestClient) -> None:
        """POST /templates/{id}/apply creates a transaction with template values."""
        ledger_id = self._create_ledger(client)
        template = self._create_template(client, ledger_id, amount="123.45")

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates/{template['id']}/apply"
        )

        data = response.json()
        assert "id" in data
        assert data["amount"] == "123.45"
        assert data["description"] == template["description"]
        assert data["from_account_id"] == template["from_account_id"]
        assert data["to_account_id"] == template["to_account_id"]
        assert data["transaction_type"] == template["transaction_type"]

    def test_apply_template_uses_today_by_default(self, client: TestClient) -> None:
        """POST /templates/{id}/apply uses today's date when no date provided."""
        ledger_id = self._create_ledger(client)
        template = self._create_template(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates/{template['id']}/apply"
        )

        data = response.json()
        assert data["date"] == date.today().isoformat()

    def test_apply_template_with_custom_date(self, client: TestClient) -> None:
        """POST /templates/{id}/apply uses provided date."""
        ledger_id = self._create_ledger(client)
        template = self._create_template(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates/{template['id']}/apply",
            json={"date": "2024-06-15"},
        )

        data = response.json()
        assert data["date"] == "2024-06-15"

    def test_apply_template_with_notes(self, client: TestClient) -> None:
        """POST /templates/{id}/apply includes notes in transaction."""
        ledger_id = self._create_ledger(client)
        template = self._create_template(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates/{template['id']}/apply",
            json={"notes": "Special occasion"},
        )

        data = response.json()
        assert data["notes"] == "Special occasion"

    def test_apply_template_nonexistent_returns_404(self, client: TestClient) -> None:
        """POST /templates/{id}/apply returns 404 for non-existent template."""
        ledger_id = self._create_ledger(client)
        fake_id = str(uuid.uuid4())

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates/{fake_id}/apply"
        )

        assert response.status_code == 404

    def test_apply_template_invalid_date_returns_422(self, client: TestClient) -> None:
        """POST /templates/{id}/apply returns 422 for invalid date format."""
        ledger_id = self._create_ledger(client)
        template = self._create_template(client, ledger_id)

        response = client.post(
            f"/api/v1/ledgers/{ledger_id}/templates/{template['id']}/apply",
            json={"date": "not-a-date"},
        )

        assert response.status_code == 422
