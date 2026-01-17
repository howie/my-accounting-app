import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.user import User


@pytest.fixture
def setup_recurring_context(session: Session):
    user = User(email="rec_test@example.com", display_name="Rec User", hashed_password="pw")
    session.add(user)
    session.commit()
    session.refresh(user)

    ledger = Ledger(name="Rec Ledger", currency="USD", user_id=user.id)
    session.add(ledger)
    session.commit()
    session.refresh(ledger)

    src = Account(name="Bank", type=AccountType.ASSET, ledger_id=ledger.id)
    dest = Account(name="Rent", type=AccountType.EXPENSE, ledger_id=ledger.id)
    session.add(src)
    session.add(dest)
    session.commit()

    return user, ledger, src, dest


class TestRecurringFlow:
    def test_recurring_lifecycle(self, client: TestClient, setup_recurring_context):
        user, ledger, src, dest = setup_recurring_context

        # 1. Create Template
        create_res = client.post(
            "/api/v1/recurring",
            json={
                "name": "Monthly Rent",
                "amount": "1200.00",
                "transaction_type": "EXPENSE",
                "source_account_id": str(src.id),
                "dest_account_id": str(dest.id),
                "frequency": "MONTHLY",
                "start_date": "2026-01-01",
            },
        )
        assert create_res.status_code == 201
        rt_id = create_res.json()["id"]

        # 2. Check Due (Assume current date is 2026-01-01 or later)
        # Note: In integration tests, we rely on the logic using current date or passing date param if supported.
        # Ideally, Check Due endpoint should accept a reference date for testing, or we rely on logic.
        # Let's assume Check Due endpoint takes an optional ?date=YYYY-MM-DD parameter for testing/simulation.

        check_res = client.get("/api/v1/recurring/due?check_date=2026-01-01")
        assert check_res.status_code == 200
        due_items = check_res.json()
        assert len(due_items) >= 1
        item = next(i for i in due_items if i["id"] == rt_id)
        assert item["due_date"] == "2026-01-01"

        # 3. Approve
        approve_res = client.post(f"/api/v1/recurring/{rt_id}/approve", json={"date": "2026-01-01"})
        assert approve_res.status_code == 201
        txn = approve_res.json()
        assert txn["amount"] == "1200.00"
        assert txn["description"] == "Monthly Rent"

        # 4. Verify no longer due for same date
        check_res_2 = client.get("/api/v1/recurring/due?check_date=2026-01-01")
        due_items_2 = check_res_2.json()
        assert not any(i["id"] == rt_id for i in due_items_2)

        # 5. Verify due next month
        check_res_3 = client.get("/api/v1/recurring/due?check_date=2026-02-01")
        due_items_3 = check_res_3.json()
        item_feb = next(i for i in due_items_3 if i["id"] == rt_id)
        assert item_feb["due_date"] == "2026-02-01"
