"""Integration tests for account query MCP tools.

Tests the full flow including database queries and edge cases.
"""

from decimal import Decimal

import pytest
from sqlmodel import Session

from src.api.mcp.tools.accounts import get_account, list_accounts
from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction, TransactionType
from src.models.user import User


@pytest.fixture
def user_with_ledger(session: Session) -> tuple[User, Ledger]:
    """Create a user with a default ledger."""
    user = User(email="test@example.com", display_name="Test User")
    session.add(user)
    session.commit()
    session.refresh(user)

    ledger = Ledger(user_id=user.id, name="個人帳本", description="測試帳本")
    session.add(ledger)
    session.commit()
    session.refresh(ledger)

    return user, ledger


@pytest.fixture
def accounts(session: Session, user_with_ledger: tuple[User, Ledger]) -> dict[str, Account]:
    """Create test accounts."""
    _, ledger = user_with_ledger

    cash = Account(
        ledger_id=ledger.id,
        name="現金",
        type=AccountType.ASSET,
        balance=Decimal("10000"),
        is_system=True,
    )
    bank = Account(
        ledger_id=ledger.id,
        name="銀行存款",
        type=AccountType.ASSET,
        balance=Decimal("50000"),
    )
    food = Account(
        ledger_id=ledger.id,
        name="餐飲",
        type=AccountType.EXPENSE,
        balance=Decimal("0"),
    )
    salary = Account(
        ledger_id=ledger.id,
        name="薪資",
        type=AccountType.INCOME,
        balance=Decimal("60000"),
    )
    credit = Account(
        ledger_id=ledger.id,
        name="信用卡",
        type=AccountType.LIABILITY,
        balance=Decimal("5000"),
    )

    session.add_all([cash, bank, food, salary, credit])
    session.commit()
    for acc in [cash, bank, food, salary, credit]:
        session.refresh(acc)

    return {
        "cash": cash,
        "bank": bank,
        "food": food,
        "salary": salary,
        "credit": credit,
    }


class TestListAccountsIntegration:
    """Integration tests for list_accounts."""

    def test_empty_ledger(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
    ):
        """Should return empty list for ledger with no accounts."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["accounts"]) == 0
        assert result["data"]["summary"]["total_assets"] == 0.0

    def test_all_account_types(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should include all account types in result."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is True
        types = {a["type"] for a in result["data"]["accounts"]}
        assert types == {"ASSET", "LIABILITY", "INCOME", "EXPENSE"}

    def test_summary_calculation(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Summary should correctly sum up balances by type."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user,
        )

        summary = result["data"]["summary"]
        assert summary["total_assets"] == 60000.0  # 10000 + 50000
        assert summary["total_liabilities"] == 5000.0
        assert summary["total_income"] == 60000.0
        assert summary["total_expenses"] == 0.0

    def test_filter_only_includes_matching_type(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Type filter should only return matching accounts."""
        user, ledger = user_with_ledger

        for type_name in ["ASSET", "LIABILITY", "INCOME", "EXPENSE"]:
            result = list_accounts(
                ledger_id=str(ledger.id),
                type_filter=type_name,
                include_zero_balance=True,
                session=session,
                user=user,
            )

            assert result["success"] is True
            for account in result["data"]["accounts"]:
                assert account["type"] == type_name


class TestGetAccountIntegration:
    """Integration tests for get_account."""

    def test_account_details(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should return correct account details."""
        user, ledger = user_with_ledger
        cash = accounts["cash"]

        result = get_account(
            account="現金",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        account = result["data"]["account"]
        assert account["id"] == str(cash.id)
        assert account["name"] == "現金"
        assert account["type"] == "ASSET"
        assert account["balance"] == 10000.0
        assert account["is_system"] is True

    def test_account_with_transactions(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should include recent transactions."""
        user, ledger = user_with_ledger
        cash = accounts["cash"]
        food = accounts["food"]

        from datetime import date

        # Create transactions
        for i in range(5):
            tx = Transaction(
                ledger_id=ledger.id,
                date=date(2026, 1, 11 - i),
                description=f"交易 {i + 1}",
                amount=Decimal("100"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
            )
            session.add(tx)
        session.commit()

        result = get_account(
            account="現金",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        recent_tx = result["data"]["account"]["recent_transactions"]
        assert len(recent_tx) == 5
        # Should be ordered by date desc
        assert recent_tx[0]["description"] == "交易 1"

    def test_recent_transactions_limit(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Recent transactions should be limited to 10."""
        user, ledger = user_with_ledger
        cash = accounts["cash"]
        food = accounts["food"]

        from datetime import date

        # Create 15 transactions
        for i in range(15):
            tx = Transaction(
                ledger_id=ledger.id,
                date=date(2026, 1, 15 - i),
                description=f"交易 {i + 1}",
                amount=Decimal("100"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
            )
            session.add(tx)
        session.commit()

        result = get_account(
            account="現金",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        recent_tx = result["data"]["account"]["recent_transactions"]
        assert len(recent_tx) == 10  # Limited to 10


class TestMultipleLedgers:
    """Test behavior with multiple ledgers."""

    def test_requires_ledger_id_when_multiple(self, session: Session):
        """Should require ledger_id when user has multiple ledgers."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        ledger1 = Ledger(user_id=user.id, name="帳本1")
        ledger2 = Ledger(user_id=user.id, name="帳本2")
        session.add_all([ledger1, ledger2])
        session.commit()

        # list_accounts without ledger_id
        result = list_accounts(
            ledger_id=None,
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "LEDGER_REQUIRED"
        assert "available_ledgers" in result["error"]

    def test_accepts_valid_ledger_id(self, session: Session):
        """Should accept valid ledger_id when user has multiple ledgers."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        ledger1 = Ledger(user_id=user.id, name="帳本1")
        ledger2 = Ledger(user_id=user.id, name="帳本2")
        session.add_all([ledger1, ledger2])
        session.commit()
        session.refresh(ledger1)

        # Add account to ledger1
        account = Account(
            ledger_id=ledger1.id,
            name="現金",
            type=AccountType.ASSET,
            balance=Decimal("1000"),
        )
        session.add(account)
        session.commit()

        result = list_accounts(
            ledger_id=str(ledger1.id),
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["accounts"]) == 1

    def test_cannot_access_other_users_ledger(self, session: Session):
        """Should not allow access to other user's ledger."""
        user1 = User(email="user1@example.com", display_name="User 1")
        user2 = User(email="user2@example.com", display_name="User 2")
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        # Create ledger for user1
        ledger1 = Ledger(user_id=user1.id, name="User1 Ledger")
        session.add(ledger1)
        session.commit()
        session.refresh(ledger1)

        # User2 tries to access user1's ledger
        result = list_accounts(
            ledger_id=str(ledger1.id),
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user2,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "LEDGER_NOT_FOUND"
