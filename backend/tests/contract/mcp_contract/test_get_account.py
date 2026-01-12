"""Contract tests for get_account MCP tool.

Tests the response format matches contracts/mcp-tools.md specification.
"""

from decimal import Decimal

import pytest
from sqlmodel import Session

from src.api.mcp.tools.accounts import get_account
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
def accounts_with_hierarchy(
    session: Session, user_with_ledger: tuple[User, Ledger]
) -> dict[str, Account]:
    """Create test accounts with parent-child hierarchy."""
    _, ledger = user_with_ledger

    # Parent account
    assets = Account(
        ledger_id=ledger.id,
        name="資產",
        type=AccountType.ASSET,
        balance=Decimal("0"),
        depth=0,
    )
    session.add(assets)
    session.commit()
    session.refresh(assets)

    # Child accounts
    cash = Account(
        ledger_id=ledger.id,
        name="現金",
        type=AccountType.ASSET,
        balance=Decimal("15000"),
        parent_id=assets.id,
        depth=1,
    )
    bank = Account(
        ledger_id=ledger.id,
        name="銀行存款",
        type=AccountType.ASSET,
        balance=Decimal("50000"),
        parent_id=assets.id,
        depth=1,
    )

    food = Account(
        ledger_id=ledger.id,
        name="餐飲",
        type=AccountType.EXPENSE,
        balance=Decimal("3500"),
        depth=1,
    )

    session.add_all([cash, bank, food])
    session.commit()
    for acc in [cash, bank, food]:
        session.refresh(acc)

    return {"assets": assets, "cash": cash, "bank": bank, "food": food}


@pytest.fixture
def transactions(
    session: Session,
    user_with_ledger: tuple[User, Ledger],
    accounts_with_hierarchy: dict[str, Account],
) -> list[Transaction]:
    """Create test transactions."""
    _, ledger = user_with_ledger
    accounts = accounts_with_hierarchy

    from datetime import date

    tx1 = Transaction(
        ledger_id=ledger.id,
        date=date(2026, 1, 11),
        description="午餐",
        amount=Decimal("85"),
        from_account_id=accounts["cash"].id,
        to_account_id=accounts["food"].id,
        transaction_type=TransactionType.EXPENSE,
    )
    tx2 = Transaction(
        ledger_id=ledger.id,
        date=date(2026, 1, 10),
        description="提款",
        amount=Decimal("3000"),
        from_account_id=accounts["bank"].id,
        to_account_id=accounts["cash"].id,
        transaction_type=TransactionType.TRANSFER,
    )
    tx3 = Transaction(
        ledger_id=ledger.id,
        date=date(2026, 1, 9),
        description="晚餐",
        amount=Decimal("120"),
        from_account_id=accounts["cash"].id,
        to_account_id=accounts["food"].id,
        transaction_type=TransactionType.EXPENSE,
    )

    session.add_all([tx1, tx2, tx3])
    session.commit()
    for tx in [tx1, tx2, tx3]:
        session.refresh(tx)

    return [tx1, tx2, tx3]


class TestGetAccountContract:
    """Contract tests for get_account response format."""

    def test_success_response_structure(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts_with_hierarchy: dict[str, Account],
    ):
        """Response should match contract success schema."""
        user, ledger = user_with_ledger

        result = get_account(
            account="現金",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        # Top-level structure
        assert "success" in result
        assert result["success"] is True
        assert "data" in result
        assert "message" in result

        # Account structure
        account = result["data"]["account"]
        assert "id" in account
        assert "name" in account
        assert "type" in account
        assert "balance" in account
        assert "parent_id" in account
        assert "depth" in account
        assert "is_system" in account
        assert "children" in account
        assert "recent_transactions" in account

    def test_account_with_children(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts_with_hierarchy: dict[str, Account],
    ):
        """Account with children should list them."""
        user, ledger = user_with_ledger

        result = get_account(
            account="資產",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        children = result["data"]["account"]["children"]
        assert len(children) == 2  # cash, bank

        # Children structure
        for child in children:
            assert "id" in child
            assert "name" in child
            assert "type" in child
            assert "balance" in child

    def test_recent_transactions_structure(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts_with_hierarchy: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Recent transactions should match contract format."""
        user, ledger = user_with_ledger

        result = get_account(
            account="現金",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        recent_tx = result["data"]["account"]["recent_transactions"]
        assert len(recent_tx) == 3  # All 3 transactions involve cash

        for tx in recent_tx:
            assert "id" in tx
            assert "date" in tx
            assert "description" in tx
            assert "amount" in tx

    def test_transaction_amount_sign(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts_with_hierarchy: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Amount should be negative when account is source."""
        user, ledger = user_with_ledger

        result = get_account(
            account="現金",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        recent_tx = result["data"]["account"]["recent_transactions"]
        # Find 午餐 transaction (cash is source)
        lunch_tx = next(tx for tx in recent_tx if tx["description"] == "午餐")
        assert lunch_tx["amount"] == -85.0  # Negative (outflow)

        # Find 提款 transaction (cash is destination)
        withdraw_tx = next(tx for tx in recent_tx if tx["description"] == "提款")
        assert withdraw_tx["amount"] == 3000.0  # Positive (inflow)

    def test_error_response_structure(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
    ):
        """Error response should match contract error schema."""
        user, ledger = user_with_ledger

        result = get_account(
            account="不存在的科目",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert "error" in result
        assert "code" in result["error"]
        assert "message" in result["error"]
        assert result["error"]["code"] == "ACCOUNT_NOT_FOUND"


class TestGetAccountLookup:
    """Test account lookup methods."""

    def test_lookup_by_name(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts_with_hierarchy: dict[str, Account],
    ):
        """Should find account by name."""
        user, ledger = user_with_ledger

        result = get_account(
            account="現金",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert result["data"]["account"]["name"] == "現金"

    def test_lookup_by_id(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts_with_hierarchy: dict[str, Account],
    ):
        """Should find account by UUID."""
        user, ledger = user_with_ledger
        cash = accounts_with_hierarchy["cash"]

        result = get_account(
            account=str(cash.id),
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert result["data"]["account"]["name"] == "現金"

    def test_default_ledger_when_single(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts_with_hierarchy: dict[str, Account],
    ):
        """Should use default ledger when user has only one."""
        user, _ = user_with_ledger

        result = get_account(
            account="現金",
            ledger_id=None,  # No ledger_id
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert result["data"]["account"]["name"] == "現金"

    def test_message_format(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts_with_hierarchy: dict[str, Account],
    ):
        """Message should include account name and balance."""
        user, ledger = user_with_ledger

        result = get_account(
            account="現金",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert "現金" in result["message"]
        assert "$15,000.00" in result["message"]
