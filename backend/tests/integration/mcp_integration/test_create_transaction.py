"""Integration tests for create_transaction MCP tool.

Tests the full flow including database persistence and account balance updates.
"""

import uuid
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from src.api.mcp.tools.transactions import create_transaction
from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction
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
    """Create test accounts for transactions."""
    _, ledger = user_with_ledger

    cash = Account(
        ledger_id=ledger.id,
        name="現金",
        type=AccountType.ASSET,
        balance=Decimal("10000"),
        is_system=True,
    )
    food = Account(
        ledger_id=ledger.id,
        name="餐飲",
        type=AccountType.EXPENSE,
        balance=Decimal("0"),
    )
    income = Account(
        ledger_id=ledger.id,
        name="薪資",
        type=AccountType.INCOME,
        balance=Decimal("0"),
    )
    bank = Account(
        ledger_id=ledger.id,
        name="銀行存款",
        type=AccountType.ASSET,
        balance=Decimal("50000"),
    )

    session.add_all([cash, food, income, bank])
    session.commit()
    for acc in [cash, food, income, bank]:
        session.refresh(acc)

    return {"cash": cash, "food": food, "income": income, "bank": bank}


class TestCreateTransactionIntegration:
    """Test create_transaction database integration."""

    def test_transaction_persisted_to_database(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Created transaction should be persisted to database."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=85.0,
            from_account="現金",
            to_account="餐飲",
            description="午餐 - 便當",
            date="2026-01-11",
            notes="測試備註",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        tx_id = uuid.UUID(result["data"]["transaction"]["id"])

        # Verify transaction exists in database
        db_tx = session.get(Transaction, tx_id)
        assert db_tx is not None
        assert db_tx.description == "午餐 - 便當"
        assert db_tx.amount == Decimal("85.00")
        assert db_tx.notes == "測試備註"

    def test_multiple_transactions_same_accounts(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Multiple transactions can be created for same accounts."""
        user, ledger = user_with_ledger

        # Create first transaction
        result1 = create_transaction(
            amount=100.0,
            from_account="現金",
            to_account="餐飲",
            description="早餐",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        # Create second transaction
        result2 = create_transaction(
            amount=150.0,
            from_account="現金",
            to_account="餐飲",
            description="午餐",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result1["success"] is True
        assert result2["success"] is True
        assert result1["data"]["transaction"]["id"] != result2["data"]["transaction"]["id"]

        # Verify both exist in database
        statement = select(Transaction).where(Transaction.ledger_id == ledger.id)
        transactions = list(session.exec(statement).all())
        assert len(transactions) == 2

    def test_transfer_between_asset_accounts(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Transfer between asset accounts should work."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=5000.0,
            from_account="銀行存款",
            to_account="現金",
            description="提款",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        tx = result["data"]["transaction"]
        assert tx["from_account"]["name"] == "銀行存款"
        assert tx["to_account"]["name"] == "現金"

    def test_income_transaction(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Income transaction from income account to asset should work."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=50000.0,
            from_account="薪資",
            to_account="銀行存款",
            description="月薪",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        tx = result["data"]["transaction"]
        assert tx["from_account"]["name"] == "薪資"
        assert tx["to_account"]["name"] == "銀行存款"


class TestCreateTransactionDefaultLedger:
    """Test create_transaction with single ledger (no ledger_id required)."""

    def test_uses_default_ledger_when_single(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should use default ledger when user has only one."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=50.0,
            from_account="現金",
            to_account="餐飲",
            description="下午茶",
            date="2026-01-11",
            notes=None,
            ledger_id=None,  # No ledger_id provided
            session=session,
            user=user,
        )

        assert result["success"] is True
        tx_id = uuid.UUID(result["data"]["transaction"]["id"])

        db_tx = session.get(Transaction, tx_id)
        assert db_tx.ledger_id == ledger.id

    def test_requires_ledger_id_when_multiple_ledgers(self, session: Session):
        """Should require ledger_id when user has multiple ledgers."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create two ledgers
        ledger1 = Ledger(user_id=user.id, name="帳本1")
        ledger2 = Ledger(user_id=user.id, name="帳本2")
        session.add_all([ledger1, ledger2])
        session.commit()

        # Create accounts in ledger1
        cash = Account(
            ledger_id=ledger1.id,
            name="現金",
            type=AccountType.ASSET,
        )
        food = Account(
            ledger_id=ledger1.id,
            name="餐飲",
            type=AccountType.EXPENSE,
        )
        session.add_all([cash, food])
        session.commit()

        result = create_transaction(
            amount=50.0,
            from_account="現金",
            to_account="餐飲",
            description="測試",
            date="2026-01-11",
            notes=None,
            ledger_id=None,  # No ledger_id provided
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "LEDGER_REQUIRED"
        assert "available_ledgers" in result["error"]
