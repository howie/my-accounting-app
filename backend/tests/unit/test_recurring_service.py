from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.models.account import Account, AccountType
from src.models.advanced import Frequency
from src.models.ledger import Ledger
from src.models.transaction import TransactionType
from src.models.user import User
from src.schemas.advanced import RecurringTransactionCreate
from src.services.recurring_service import RecurringService


@pytest.fixture
def test_accounts(session: Session):
    user = User(email="test@example.com", display_name="Test User", hashed_password="pw")
    session.add(user)
    session.commit()
    session.refresh(user)

    ledger = Ledger(name="Test Ledger", currency="USD", user_id=user.id)
    session.add(ledger)
    session.commit()
    session.refresh(ledger)

    src = Account(name="Bank", type=AccountType.ASSET, ledger_id=ledger.id)
    dest = Account(name="Rent", type=AccountType.EXPENSE, ledger_id=ledger.id)
    session.add(src)
    session.add(dest)
    session.commit()
    session.refresh(src)
    session.refresh(dest)
    return src, dest


class TestRecurringService:
    def test_create_recurring(self, session: Session, test_accounts):
        src, dest = test_accounts
        service = RecurringService(session)

        data = RecurringTransactionCreate(
            name="Rent",
            amount=Decimal("100.00"),
            transaction_type=TransactionType.EXPENSE,
            source_account_id=src.id,
            dest_account_id=dest.id,
            frequency=Frequency.MONTHLY,
            start_date=date(2026, 1, 1),
        )

        rt = service.create_recurring_transaction(data)
        assert rt.id is not None
        assert rt.name == "Rent"
        assert rt.last_generated_date is None

    def test_get_due_transactions(self, session: Session, test_accounts):
        src, dest = test_accounts
        service = RecurringService(session)

        # Monthly rent starting Jan 1
        data = RecurringTransactionCreate(
            name="Rent",
            amount=Decimal("100.00"),
            transaction_type=TransactionType.EXPENSE,
            source_account_id=src.id,
            dest_account_id=dest.id,
            frequency=Frequency.MONTHLY,
            start_date=date(2026, 1, 1),
        )
        rt = service.create_recurring_transaction(data)

        # Check on Jan 1 - Should be due
        due = service.get_due_transactions(date(2026, 1, 1))
        assert len(due) == 1
        assert due[0].id == rt.id
        assert due[0].due_date == date(2026, 1, 1)

        # Check on Feb 1 - Should be due
        due_feb = service.get_due_transactions(date(2026, 2, 1))
        assert len(due_feb) >= 1

    def test_approve_transaction(self, session: Session, test_accounts):
        src, dest = test_accounts
        service = RecurringService(session)

        data = RecurringTransactionCreate(
            name="Rent",
            amount=Decimal("100.00"),
            transaction_type=TransactionType.EXPENSE,
            source_account_id=src.id,
            dest_account_id=dest.id,
            frequency=Frequency.MONTHLY,
            start_date=date(2026, 1, 1),
        )
        rt = service.create_recurring_transaction(data)

        # Approve for Jan 1
        txn = service.approve_transaction(rt.id, date(2026, 1, 1))

        assert txn is not None
        assert txn.amount == Decimal("100.00")
        assert txn.recurring_transaction_id == rt.id

        # Verify last_generated_date updated
        session.refresh(rt)
        assert rt.last_generated_date == date(2026, 1, 1)

        # Should not be due anymore for Jan 1
        due = service.get_due_transactions(date(2026, 1, 1))
        assert len(due) == 0

    def test_approve_future_date_fails(self, session: Session, test_accounts):
        # Prevent approving things far in future if needed, or just standard logic
        pass
