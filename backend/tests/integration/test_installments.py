from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.user import User


@pytest.fixture
def setup_installment_context(session: Session):
    user = User(email="inst_test@example.com", display_name="Inst User", hashed_password="pw")
    session.add(user)
    session.commit()
    session.refresh(user)

    ledger = Ledger(name="Inst Ledger", currency="USD", user_id=user.id)
    session.add(ledger)
    session.commit()
    session.refresh(ledger)

    src = Account(name="Credit Card", type=AccountType.LIABILITY, ledger_id=ledger.id)
    dest = Account(name="Laptop", type=AccountType.ASSET, ledger_id=ledger.id)
    session.add(src)
    session.add(dest)
    session.commit()

    return user, ledger, src, dest


class TestInstallmentFlow:
    def test_create_installment_plan(self, client: TestClient, setup_installment_context):
        user, ledger, src, dest = setup_installment_context

        response = client.post(
            "/api/v1/installments",
            json={
                "name": "New Laptop",
                "total_amount": "1200.00",
                "installment_count": 12,
                "source_account_id": str(src.id),
                "dest_account_id": str(dest.id),
                "start_date": "2026-01-15",
            },
        )
        assert response.status_code == 201
        data = response.json()
        plan_id = data["id"]

        # Verify transactions generated in Ledger
        # Assuming we can list transactions by ledger
        txn_res = client.get(f"/api/v1/ledgers/{ledger.id}/transactions?limit=100")
        assert txn_res.status_code == 200
        txns = txn_res.json()["data"]

        # Filter for this plan (assuming we can identify them, e.g. by description or if API exposes plan_id in txn list)
        plan_txns = [t for t in txns if "New Laptop" in t["description"]]
        assert len(plan_txns) == 12

        # Sum validation
        total = sum(Decimal(t["amount"]) for t in plan_txns)
        assert total == Decimal("1200.00")

        # Audit linking check (if exposed in API)
        # Assuming TransactionRead includes installment_plan_id or we check DB if not exposed.
        # For integration test using public API, we rely on observable behavior or extended response schema.
        # Let's assume description contains "(1/12)" etc as per service logic.
        assert any("(1/12)" in t["description"] for t in plan_txns)
        assert any("(12/12)" in t["description"] for t in plan_txns)
