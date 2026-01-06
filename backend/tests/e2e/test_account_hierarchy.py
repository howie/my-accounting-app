"""E2E tests for Account Hierarchy (TC-HIR-xxx).

Tests hierarchical account structure (up to 3 levels).
"""

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from tests.e2e.conftest import E2ETestHelper


class TestAccountHierarchy:
    """TC-HIR: Account Hierarchy tests."""

    def test_hir_001_create_child_account_level_2(self, setup_user_and_ledger: E2ETestHelper):
        """TC-HIR-001: Create child account (level 2)."""
        helper = setup_user_and_ledger

        # Create parent
        parent = helper.create_account("Living Expenses", "EXPENSE")
        assert parent["depth"] == 1

        # Create child
        child = helper.create_account("Utilities", "EXPENSE", parent_id=parent["id"])

        assert child["name"] == "Utilities"
        assert child["depth"] == 2
        assert child["parent_id"] == parent["id"]
        assert child["type"] == "EXPENSE"

    def test_hir_002_create_grandchild_account_level_3(
        self, setup_user_and_ledger: E2ETestHelper
    ):
        """TC-HIR-002: Create grandchild account (level 3)."""
        helper = setup_user_and_ledger

        # Create hierarchy: Living Expenses -> Utilities -> Electricity
        root = helper.create_account("Living Expenses", "EXPENSE")
        child = helper.create_account("Utilities", "EXPENSE", parent_id=root["id"])
        grandchild = helper.create_account("Electricity", "EXPENSE", parent_id=child["id"])

        assert grandchild["depth"] == 3
        assert grandchild["parent_id"] == child["id"]

    def test_hir_003_max_depth_exceeded_rejected(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """TC-HIR-003: Cannot create account beyond max depth (3)."""
        helper = setup_user_and_ledger

        # Create 3-level hierarchy
        level1 = helper.create_account("Level 1", "EXPENSE")
        level2 = helper.create_account("Level 2", "EXPENSE", parent_id=level1["id"])
        level3 = helper.create_account("Level 3", "EXPENSE", parent_id=level2["id"])

        # Try to create level 4 - should fail
        response = client.post(
            f"/api/v1/ledgers/{helper.ledger_id}/accounts",
            json={"name": "Level 4", "type": "EXPENSE", "parent_id": level3["id"]},
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 400
        assert "depth" in response.json()["detail"].lower()

    def test_hir_004_parent_type_mismatch_rejected(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """TC-HIR-004: Child must have same type as parent."""
        helper = setup_user_and_ledger

        # Create EXPENSE parent
        parent = helper.create_account("Food", "EXPENSE")

        # Try to create INCOME child - should fail
        response = client.post(
            f"/api/v1/ledgers/{helper.ledger_id}/accounts",
            json={"name": "Income Child", "type": "INCOME", "parent_id": parent["id"]},
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 400
        assert "type" in response.json()["detail"].lower()

    def test_hir_005_get_account_tree(self, setup_user_and_ledger: E2ETestHelper):
        """TC-HIR-005: Get hierarchical account tree."""
        helper = setup_user_and_ledger

        # Create hierarchy
        food = helper.create_account("Food", "EXPENSE")
        groceries = helper.create_account("Groceries", "EXPENSE", parent_id=food["id"])
        restaurants = helper.create_account("Restaurants", "EXPENSE", parent_id=food["id"])

        # Get tree
        tree = helper.get_account_tree()

        # Find Food in tree
        food_node = None
        for node in tree:
            if node["name"] == "Food":
                food_node = node
                break

        assert food_node is not None
        assert "children" in food_node
        assert len(food_node["children"]) == 2

        child_names = [c["name"] for c in food_node["children"]]
        assert "Groceries" in child_names
        assert "Restaurants" in child_names

    def test_hir_006_delete_parent_with_children_rejected(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """TC-HIR-006: Cannot delete parent account that has children."""
        helper = setup_user_and_ledger

        # Create parent with child
        parent = helper.create_account("Parent", "EXPENSE")
        helper.create_account("Child", "EXPENSE", parent_id=parent["id"])

        # Try to delete parent
        response = client.delete(
            f"/api/v1/ledgers/{helper.ledger_id}/accounts/{parent['id']}",
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 409
        assert "child" in response.json()["detail"].lower()

    def test_hir_007_balance_aggregation_in_tree(self, setup_user_and_ledger: E2ETestHelper):
        """TC-HIR-007: Parent balance aggregates child balances."""
        helper = setup_user_and_ledger

        # Create hierarchy
        food = helper.create_account("Food", "EXPENSE")
        groceries = helper.create_account("Groceries", "EXPENSE", parent_id=food["id"])
        restaurants = helper.create_account("Restaurants", "EXPENSE", parent_id=food["id"])

        # Get Cash account
        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)

        # Create transactions to child accounts
        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=groceries["id"],
            amount=100.0,
            transaction_type="EXPENSE",
            description="Groceries expense",
        )

        helper.create_transaction(
            from_account_id=cash["id"],
            to_account_id=restaurants["id"],
            amount=50.0,
            transaction_type="EXPENSE",
            description="Restaurant expense",
        )

        # Get tree and verify aggregation
        tree = helper.get_account_tree()

        food_node = None
        for node in tree:
            if node["name"] == "Food":
                food_node = node
                break

        assert food_node is not None
        # Parent should show aggregated balance of 150
        assert Decimal(food_node["balance"]) == Decimal("150.00")

        # Children should show individual balances
        for child in food_node["children"]:
            if child["name"] == "Groceries":
                assert Decimal(child["balance"]) == Decimal("100.00")
            elif child["name"] == "Restaurants":
                assert Decimal(child["balance"]) == Decimal("50.00")

    def test_hir_008_transaction_on_parent_rejected(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """TC-HIR-008: Cannot create transaction on parent account (non-leaf)."""
        helper = setup_user_and_ledger

        # Create parent with child
        parent = helper.create_account("Parent", "EXPENSE")
        helper.create_account("Child", "EXPENSE", parent_id=parent["id"])

        # Get Cash account
        accounts = helper.list_accounts()
        cash = helper.find_account_by_name("Cash", accounts)

        # Try to create transaction to parent (has children)
        response = client.post(
            f"/api/v1/ledgers/{helper.ledger_id}/transactions",
            json={
                "from_account_id": cash["id"],
                "to_account_id": parent["id"],
                "amount": 50.0,
                "transaction_type": "EXPENSE",
                "description": "Should fail",
                "date": "2024-01-15",
            },
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 400
        assert "leaf" in response.json()["detail"].lower() or "child" in response.json()["detail"].lower()

    def test_hir_009_parent_in_different_ledger_rejected(
        self, e2e_helper: E2ETestHelper, client: TestClient
    ):
        """Parent must be in same ledger."""
        e2e_helper.setup_user(f"hir-test-{uuid.uuid4()}@example.com")

        # Create ledger 1 with account
        e2e_helper.create_ledger("Ledger One", 100.0)
        parent = e2e_helper.create_account("Parent", "EXPENSE")

        # Create ledger 2
        e2e_helper.create_ledger("Ledger Two", 200.0)
        ledger2_id = e2e_helper.ledger_id

        # Try to create child in ledger 2 with parent from ledger 1
        response = client.post(
            f"/api/v1/ledgers/{ledger2_id}/accounts",
            json={"name": "Child", "type": "EXPENSE", "parent_id": parent["id"]},
            headers={"X-User-ID": e2e_helper.user_id},
        )

        assert response.status_code == 400

    def test_hir_010_has_children_flag(self, setup_user_and_ledger: E2ETestHelper):
        """Account has_children flag is set correctly."""
        helper = setup_user_and_ledger

        # Create parent and child
        parent = helper.create_account("Parent", "EXPENSE")
        assert parent["has_children"] is False  # Initially no children

        # Add child
        helper.create_account("Child", "EXPENSE", parent_id=parent["id"])

        # Refresh parent - should now have children
        updated_parent = helper.get_account(parent["id"])
        assert updated_parent["has_children"] is True

    def test_hir_011_three_level_hierarchy_full(self, setup_user_and_ledger: E2ETestHelper):
        """Complete 3-level hierarchy with transactions and balance check."""
        helper = setup_user_and_ledger

        # Create full 3-level hierarchy
        level1 = helper.create_account("Living Expenses", "EXPENSE")
        level2 = helper.create_account("Utilities", "EXPENSE", parent_id=level1["id"])
        electricity = helper.create_account("Electricity", "EXPENSE", parent_id=level2["id"])
        water = helper.create_account("Water", "EXPENSE", parent_id=level2["id"])

        # Get Cash
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

        # Get tree and verify cascade
        tree = helper.get_account_tree()

        living = None
        for node in tree:
            if node["name"] == "Living Expenses":
                living = node
                break

        assert living is not None
        # Level 1 aggregates all: 100 + 30 = 130
        assert Decimal(living["balance"]) == Decimal("130.00")

        # Find Utilities in children
        utilities = None
        for child in living["children"]:
            if child["name"] == "Utilities":
                utilities = child
                break

        assert utilities is not None
        # Level 2 also aggregates: 130
        assert Decimal(utilities["balance"]) == Decimal("130.00")

        # Leaf accounts have direct balances
        for leaf in utilities["children"]:
            if leaf["name"] == "Electricity":
                assert Decimal(leaf["balance"]) == Decimal("100.00")
            elif leaf["name"] == "Water":
                assert Decimal(leaf["balance"]) == Decimal("30.00")

    def test_hir_012_tree_filtered_by_type(
        self, setup_user_and_ledger: E2ETestHelper, client: TestClient
    ):
        """Account tree can be filtered by type."""
        helper = setup_user_and_ledger

        # Create accounts of different types
        helper.create_account("Food", "EXPENSE")
        helper.create_account("Salary", "INCOME")

        # Get tree filtered by EXPENSE
        response = client.get(
            f"/api/v1/ledgers/{helper.ledger_id}/accounts/tree?type=EXPENSE",
            headers={"X-User-ID": helper.user_id},
        )

        assert response.status_code == 200
        tree = response.json()["data"]

        # Should only have EXPENSE accounts
        for node in tree:
            assert node["type"] == "EXPENSE"
