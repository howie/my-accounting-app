"""Edge case tests for create_transaction MCP tool.

Tests invalid inputs, fuzzy matching, and error scenarios.
"""

from decimal import Decimal

import pytest
from sqlmodel import Session

from src.api.mcp.tools.transactions import create_transaction
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
    breakfast = Account(
        ledger_id=ledger.id,
        name="早午餐",
        type=AccountType.EXPENSE,
        balance=Decimal("0"),
    )
    dining = Account(
        ledger_id=ledger.id,
        name="外食",
        type=AccountType.EXPENSE,
        balance=Decimal("0"),
    )

    session.add_all([cash, food, breakfast, dining])
    session.commit()
    for acc in [cash, food, breakfast, dining]:
        session.refresh(acc)

    return {"cash": cash, "food": food, "breakfast": breakfast, "dining": dining}


class TestInvalidAmount:
    """Test invalid amount handling."""

    def test_negative_amount_fails(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Negative amounts should fail validation."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=-100.0,
            from_account="現金",
            to_account="餐飲",
            description="測試",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_AMOUNT"

    def test_zero_amount_fails(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Zero amounts should fail validation."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=0.0,
            from_account="現金",
            to_account="餐飲",
            description="測試",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_AMOUNT"

    def test_amount_too_large_fails(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Amount exceeding max should fail validation."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=9999999999.99 + 1,  # Over max per contract
            from_account="現金",
            to_account="餐飲",
            description="測試",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_AMOUNT"


class TestAccountNotFound:
    """Test account not found handling with suggestions."""

    def test_from_account_not_found_suggests_similar(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Missing from_account should suggest similar names."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=100.0,
            from_account="現款",  # Typo for 現金
            to_account="餐飲",
            description="測試",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "ACCOUNT_NOT_FOUND"
        assert "suggestions" in result["error"]
        assert "現金" in result["error"]["suggestions"]

    def test_to_account_not_found_suggests_similar(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Missing to_account should suggest similar names."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=100.0,
            from_account="現金",
            to_account="早餐",  # Not exactly matching any account
            description="測試",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "ACCOUNT_NOT_FOUND"
        assert "suggestions" in result["error"]
        # Should suggest 餐飲, 早午餐, 外食
        suggestions = result["error"]["suggestions"]
        assert len(suggestions) > 0


class TestFuzzyMatching:
    """Test account fuzzy matching."""

    def test_partial_name_match(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Partial account names should match."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=100.0,
            from_account="現金",
            to_account="餐",  # Partial match for 餐飲
            description="測試",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        # Either succeeds with fuzzy match or fails with suggestions
        if result["success"]:
            assert result["data"]["transaction"]["to_account"]["name"] == "餐飲"
        else:
            assert result["error"]["code"] == "ACCOUNT_NOT_FOUND"
            assert "餐飲" in result["error"]["suggestions"]


class TestInvalidDate:
    """Test invalid date handling."""

    def test_invalid_date_format_fails(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Invalid date format should fail."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=100.0,
            from_account="現金",
            to_account="餐飲",
            description="測試",
            date="01-11-2026",  # Wrong format
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_DATE"

    def test_nonexistent_date_fails(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Nonexistent date should fail."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=100.0,
            from_account="現金",
            to_account="餐飲",
            description="測試",
            date="2026-02-30",  # Feb 30 doesn't exist
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_DATE"


class TestSameAccountError:
    """Test same from/to account error."""

    def test_same_account_fails(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Transaction with same from and to account should fail."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=100.0,
            from_account="現金",
            to_account="現金",
            description="測試",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"


class TestDescriptionValidation:
    """Test description validation."""

    def test_empty_description_fails(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Empty description should fail."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=100.0,
            from_account="現金",
            to_account="餐飲",
            description="",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"

    def test_description_too_long_fails(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Description over 255 chars should fail."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=100.0,
            from_account="現金",
            to_account="餐飲",
            description="a" * 256,
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"
