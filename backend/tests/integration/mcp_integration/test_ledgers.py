"""Integration tests for list_ledgers MCP tool.

Tests the full flow including database queries.
"""

from decimal import Decimal

import pytest
from sqlmodel import Session

from src.api.mcp.tools.ledgers import list_ledgers
from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.user import User


@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(email="test@example.com", display_name="Test User")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestListLedgersIntegration:
    """Integration tests for list_ledgers."""

    def test_multiple_users_isolation(self, session: Session):
        """Each user should only see their own ledgers."""
        user1 = User(email="user1@example.com", display_name="User 1")
        user2 = User(email="user2@example.com", display_name="User 2")
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        # Create ledgers for each user
        ledger1 = Ledger(user_id=user1.id, name="User1 帳本")
        ledger2 = Ledger(user_id=user2.id, name="User2 帳本")
        session.add_all([ledger1, ledger2])
        session.commit()

        # User1 should only see their ledger
        result1 = list_ledgers(session=session, user=user1)
        assert result1["success"] is True
        assert len(result1["data"]["ledgers"]) == 1
        assert result1["data"]["ledgers"][0]["name"] == "User1 帳本"

        # User2 should only see their ledger
        result2 = list_ledgers(session=session, user=user2)
        assert result2["success"] is True
        assert len(result2["data"]["ledgers"]) == 1
        assert result2["data"]["ledgers"][0]["name"] == "User2 帳本"

    def test_account_count_accuracy(
        self,
        session: Session,
        user: User,
    ):
        """Account count should be accurate."""
        ledger = Ledger(user_id=user.id, name="測試帳本")
        session.add(ledger)
        session.commit()
        session.refresh(ledger)

        # Add 5 accounts
        for i in range(5):
            account = Account(
                ledger_id=ledger.id,
                name=f"科目 {i + 1}",
                type=AccountType.ASSET,
                balance=Decimal("0"),
            )
            session.add(account)
        session.commit()

        result = list_ledgers(session=session, user=user)
        assert result["data"]["ledgers"][0]["account_count"] == 5

    def test_transaction_count_accuracy(
        self,
        session: Session,
        user: User,
    ):
        """Transaction count should be accurate."""
        from datetime import date

        from src.models.transaction import Transaction, TransactionType

        ledger = Ledger(user_id=user.id, name="測試帳本")
        session.add(ledger)
        session.commit()
        session.refresh(ledger)

        # Add accounts
        cash = Account(
            ledger_id=ledger.id,
            name="現金",
            type=AccountType.ASSET,
            balance=Decimal("10000"),
        )
        food = Account(
            ledger_id=ledger.id,
            name="餐飲",
            type=AccountType.EXPENSE,
            balance=Decimal("0"),
        )
        session.add_all([cash, food])
        session.commit()
        session.refresh(cash)
        session.refresh(food)

        # Add 10 transactions
        for i in range(10):
            tx = Transaction(
                ledger_id=ledger.id,
                date=date(2026, 1, i + 1),
                description=f"交易 {i + 1}",
                amount=Decimal("100"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
            )
            session.add(tx)
        session.commit()

        result = list_ledgers(session=session, user=user)
        assert result["data"]["ledgers"][0]["transaction_count"] == 10

    def test_empty_ledger_counts(
        self,
        session: Session,
        user: User,
    ):
        """Empty ledger should have zero counts."""
        ledger = Ledger(user_id=user.id, name="空帳本")
        session.add(ledger)
        session.commit()

        result = list_ledgers(session=session, user=user)
        assert result["data"]["ledgers"][0]["account_count"] == 0
        assert result["data"]["ledgers"][0]["transaction_count"] == 0

    def test_ledger_ordering(
        self,
        session: Session,
        user: User,
    ):
        """Ledgers should be returned in creation order."""

        ledger1 = Ledger(user_id=user.id, name="第一個帳本")
        session.add(ledger1)
        session.commit()

        ledger2 = Ledger(user_id=user.id, name="第二個帳本")
        session.add(ledger2)
        session.commit()

        ledger3 = Ledger(user_id=user.id, name="第三個帳本")
        session.add(ledger3)
        session.commit()

        result = list_ledgers(session=session, user=user)
        names = [l["name"] for l in result["data"]["ledgers"]]
        assert names == ["第一個帳本", "第二個帳本", "第三個帳本"]
