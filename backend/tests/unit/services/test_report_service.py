"""Unit tests for ReportService."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction, TransactionType
from src.models.user import User
from src.services.report_service import ReportService


@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(email="test@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def ledger(session: Session, user: User) -> Ledger:
    """Create a test ledger."""
    ledger = Ledger(name="Test Ledger", currency="USD", user_id=user.id)
    session.add(ledger)
    session.commit()
    session.refresh(ledger)
    return ledger


@pytest.fixture
def accounts(session: Session, ledger: Ledger) -> dict[str, Account]:
    """Create test accounts."""
    asset = Account(name="Assets", type=AccountType.ASSET, ledger_id=ledger.id, depth=1)
    cash = Account(name="Cash", type=AccountType.ASSET, ledger_id=ledger.id, parent=asset, depth=2)
    expense = Account(name="Expenses", type=AccountType.EXPENSE, ledger_id=ledger.id, depth=1)
    food = Account(
        name="Food", type=AccountType.EXPENSE, ledger_id=ledger.id, parent=expense, depth=2
    )
    income = Account(name="Income", type=AccountType.INCOME, ledger_id=ledger.id, depth=1)
    salary = Account(
        name="Salary", type=AccountType.INCOME, ledger_id=ledger.id, parent=income, depth=2
    )

    session.add_all([asset, cash, expense, food, income, salary])
    session.commit()
    return {
        "asset": asset,
        "cash": cash,
        "expense": expense,
        "food": food,
        "income": income,
        "salary": salary,
    }


@pytest.fixture
def report_service(session: Session) -> ReportService:
    return ReportService(session)


def create_transaction(
    session: Session,
    ledger_id: str,
    date_val: date,
    amount: Decimal,
    from_acc: Account,
    to_acc: Account,
):
    tx = Transaction(
        ledger_id=ledger_id,
        date=date_val,
        description="Test Tx",
        amount=amount,
        from_account_id=from_acc.id,
        to_account_id=to_acc.id,
        transaction_type=TransactionType.EXPENSE,  # Type doesn't strictly matter for balance calc
    )
    session.add(tx)
    session.commit()
    return tx


@pytest.mark.asyncio
async def test_get_account_balances_at_date(
    session: Session, ledger: Ledger, accounts: dict[str, Account], report_service: ReportService
):
    # Setup transactions
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    # Yesterday: Salary -> Cash 1000
    create_transaction(
        session, ledger.id, yesterday, Decimal("1000"), accounts["salary"], accounts["cash"]
    )

    # Today: Cash -> Food 50
    create_transaction(session, ledger.id, today, Decimal("50"), accounts["cash"], accounts["food"])

    # Tomorrow: Cash -> Food 20
    create_transaction(
        session, ledger.id, tomorrow, Decimal("20"), accounts["cash"], accounts["food"]
    )

    # Test Balance at Yesterday
    balances_yesterday = await report_service.get_account_balances_at_date(ledger.id, yesterday)
    # Cash: +1000
    assert balances_yesterday.get(accounts["cash"].id) == Decimal("1000")

    # Test Balance at Today
    balances_today = await report_service.get_account_balances_at_date(ledger.id, today)
    # Cash: 1000 - 50 = 950
    assert balances_today.get(accounts["cash"].id) == Decimal("950")
    # Food: +50
    assert balances_today.get(accounts["food"].id) == Decimal("50")

    # Test Balance at Tomorrow
    balances_tomorrow = await report_service.get_account_balances_at_date(ledger.id, tomorrow)
    # Cash: 950 - 20 = 930
    assert balances_tomorrow.get(accounts["cash"].id) == Decimal("930")


@pytest.mark.asyncio
async def test_future_dates_behavior(
    session: Session, ledger: Ledger, accounts: dict[str, Account], report_service: ReportService
):
    """Ensure requests for future dates include all transactions up to that date."""
    future_date = date.today() + timedelta(days=365)
    create_transaction(
        session, ledger.id, future_date, Decimal("100"), accounts["salary"], accounts["cash"]
    )

    balances = await report_service.get_account_balances_at_date(ledger.id, future_date)
    assert balances.get(accounts["cash"].id) == Decimal("100")


@pytest.mark.asyncio
async def test_zero_balances(
    session: Session,  # noqa: ARG001
    ledger: Ledger,
    accounts: dict[str, Account],
    report_service: ReportService,
):
    """Ensure accounts with zero balance are handled (service returns them as 0 or missing, tree builder handles display)."""
    # No transactions
    balances = await report_service.get_account_balances_at_date(ledger.id, date.today())
    assert balances.get(accounts["cash"].id, Decimal("0")) == Decimal("0")


def test_build_report_hierarchy(
    ledger: Ledger,  # noqa: ARG001
    accounts: dict[str, Account],
    report_service: ReportService,
):
    """Test hierarchy building."""
    balances = {
        accounts["cash"].id: Decimal("100"),
        accounts["food"].id: Decimal("50"),
    }

    # Build Assets tree
    all_accounts = list(accounts.values())
    asset_tree = report_service.build_report_hierarchy(
        all_accounts, balances, root_type=AccountType.ASSET
    )

    assert len(asset_tree) == 1
    root = asset_tree[0]
    assert root.name == "Assets"
    assert root.amount == Decimal("100")  # Aggregated from children
    assert len(root.children) == 1
    child = root.children[0]
    assert child.name == "Cash"
    assert child.amount == Decimal("100")
