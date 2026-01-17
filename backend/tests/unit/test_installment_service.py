from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction
from src.models.user import User
from src.schemas.advanced import InstallmentPlanCreate
from src.services.installment_service import InstallmentService


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

    src = Account(name="Credit Card", type=AccountType.LIABILITY, ledger_id=ledger.id)
    dest = Account(name="Computer", type=AccountType.ASSET, ledger_id=ledger.id)
    session.add(src)
    session.add(dest)
    session.commit()
    session.refresh(src)
    session.refresh(dest)
    return src, dest


class TestInstallmentService:
    def test_create_installment_plan(self, session: Session, test_accounts):
        src, dest = test_accounts
        service = InstallmentService(session)

        data = InstallmentPlanCreate(
            name="Laptop",
            total_amount=Decimal("1200.00"),
            installment_count=12,
            source_account_id=src.id,
            dest_account_id=dest.id,
            start_date=date(2026, 1, 15),
        )

        plan = service.create_installment_plan(data)

        assert plan.id is not None
        assert plan.total_amount == Decimal("1200.00")
        assert plan.installment_count == 12

        # Verify transactions generated
        txns = session.exec(
            select(Transaction).where(Transaction.installment_plan_id == plan.id)
        ).all()
        assert len(txns) == 12

        # Verify sum matches total (DI-001)
        total_generated = sum(t.amount for t in txns)
        assert total_generated == Decimal("1200.00")

        # Verify dates
        # Assuming monthly by default for MVP
        assert txns[0].date == date(2026, 1, 15)
        assert txns[1].date == date(2026, 2, 15)

        # Verify installment numbers
        assert txns[0].installment_number == 1
        assert txns[11].installment_number == 12

    def test_create_installment_plan_rounding(self, session: Session, test_accounts):
        src, dest = test_accounts
        service = InstallmentService(session)

        # 100 / 3 = 33.333...
        data = InstallmentPlanCreate(
            name="Split 100",
            total_amount=Decimal("100.00"),
            installment_count=3,
            source_account_id=src.id,
            dest_account_id=dest.id,
            start_date=date(2026, 1, 1),
        )

        plan = service.create_installment_plan(data)

        txns = session.exec(
            select(Transaction).where(Transaction.installment_plan_id == plan.id)
        ).all()
        assert len(txns) == 3

        total_generated = sum(t.amount for t in txns)
        assert total_generated == Decimal("100.00")

        # Should be 33.33, 33.33, 33.34 (or similar distribution)
        amounts = sorted([t.amount for t in txns])
        assert amounts == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
