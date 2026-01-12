"""Edge case tests for account query MCP tools.

Tests error handling, boundary conditions, and special scenarios.
"""

from decimal import Decimal

import pytest
from sqlmodel import Session

from src.api.mcp.tools.accounts import get_account, list_accounts
from src.models.account import Account, AccountType
from src.models.ledger import Ledger
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
    )
    food = Account(
        ledger_id=ledger.id,
        name="餐飲",
        type=AccountType.EXPENSE,
        balance=Decimal("5000"),
    )

    session.add_all([cash, food])
    session.commit()
    for acc in [cash, food]:
        session.refresh(acc)

    return {"cash": cash, "food": food}


class TestListAccountsEdgeCases:
    """Edge case tests for list_accounts."""

    def test_user_with_no_ledgers(self, session: Session):
        """Should return error when user has no ledgers."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        result = list_accounts(
            ledger_id=None,
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "LEDGER_NOT_FOUND"
        assert "帳本" in result["error"]["message"]

    def test_invalid_ledger_id_format(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
    ):
        """Should return validation error for invalid UUID."""
        user, _ = user_with_ledger

        result = list_accounts(
            ledger_id="not-a-uuid",
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"

    def test_nonexistent_ledger_id(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
    ):
        """Should return error for valid UUID that doesn't exist."""
        user, _ = user_with_ledger
        import uuid

        result = list_accounts(
            ledger_id=str(uuid.uuid4()),  # Random valid UUID
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "LEDGER_NOT_FOUND"

    def test_invalid_type_filter(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should return validation error for invalid type filter."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter="INVALID_TYPE",
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert "ASSET" in result["error"]["message"]  # Should list valid types

    def test_case_sensitive_type_filter(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Type filter should be case sensitive (uppercase required)."""
        user, ledger = user_with_ledger

        # Lowercase should fail
        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter="asset",  # lowercase
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"

    def test_empty_result_with_type_filter(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should return empty list when no accounts match filter."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter="LIABILITY",  # No liability accounts exist
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["accounts"]) == 0

    def test_all_zero_balance_excluded(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
    ):
        """Should return empty list when all accounts have zero balance."""
        user, ledger = user_with_ledger

        # Create accounts with zero balance
        zero_account = Account(
            ledger_id=ledger.id,
            name="空帳戶",
            type=AccountType.ASSET,
            balance=Decimal("0"),
        )
        session.add(zero_account)
        session.commit()

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter=None,
            include_zero_balance=False,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["accounts"]) == 0


class TestGetAccountEdgeCases:
    """Edge case tests for get_account."""

    def test_account_not_found_by_name(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should return error when account name doesn't exist."""
        user, ledger = user_with_ledger

        result = get_account(
            account="不存在的科目",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "ACCOUNT_NOT_FOUND"
        assert "不存在的科目" in result["error"]["message"]

    def test_account_not_found_by_id(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should return error when account UUID doesn't exist."""
        user, ledger = user_with_ledger
        import uuid

        result = get_account(
            account=str(uuid.uuid4()),  # Random UUID
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "ACCOUNT_NOT_FOUND"

    def test_user_with_no_ledgers(self, session: Session):
        """Should return error when user has no ledgers."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        result = get_account(
            account="現金",
            ledger_id=None,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "LEDGER_NOT_FOUND"

    def test_account_in_different_ledger(self, session: Session):
        """Should not find account that exists in different ledger."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create two ledgers
        ledger1 = Ledger(user_id=user.id, name="帳本1")
        ledger2 = Ledger(user_id=user.id, name="帳本2")
        session.add_all([ledger1, ledger2])
        session.commit()
        session.refresh(ledger1)
        session.refresh(ledger2)

        # Create account in ledger1
        account = Account(
            ledger_id=ledger1.id,
            name="現金",
            type=AccountType.ASSET,
            balance=Decimal("1000"),
        )
        session.add(account)
        session.commit()

        # Try to find account in ledger2
        result = get_account(
            account="現金",
            ledger_id=str(ledger2.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "ACCOUNT_NOT_FOUND"

    def test_account_with_no_transactions(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should return empty recent_transactions list."""
        user, ledger = user_with_ledger

        result = get_account(
            account="現金",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert result["data"]["account"]["recent_transactions"] == []

    def test_account_with_no_children(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should return empty children list."""
        user, ledger = user_with_ledger

        result = get_account(
            account="現金",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert result["data"]["account"]["children"] == []

    def test_invalid_ledger_id_format(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
    ):
        """Should return validation error for invalid ledger UUID."""
        user, _ = user_with_ledger

        result = get_account(
            account="現金",
            ledger_id="invalid-uuid",
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"

    def test_unicode_account_name(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
    ):
        """Should handle unicode characters in account names."""
        user, ledger = user_with_ledger

        # Create account with special characters
        account = Account(
            ledger_id=ledger.id,
            name="🏠 房租支出",
            type=AccountType.EXPENSE,
            balance=Decimal("20000"),
        )
        session.add(account)
        session.commit()

        result = get_account(
            account="🏠 房租支出",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert result["data"]["account"]["name"] == "🏠 房租支出"

    def test_decimal_balance_precision(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
    ):
        """Should preserve decimal precision in balance."""
        user, ledger = user_with_ledger

        # Create account with precise decimal balance
        account = Account(
            ledger_id=ledger.id,
            name="精確餘額",
            type=AccountType.ASSET,
            balance=Decimal("12345.67"),
        )
        session.add(account)
        session.commit()

        result = get_account(
            account="精確餘額",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert result["data"]["account"]["balance"] == 12345.67
