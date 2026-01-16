"""Contract tests for Reports API."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction, TransactionType
from src.models.user import User


@pytest.fixture
def user(session: Session) -> User:
    user = User(email="contract@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def ledger(session: Session, user: User) -> Ledger:
    ledger = Ledger(name="Contract Ledger", currency="USD", user_id=user.id)
    session.add(ledger)
    session.commit()
    session.refresh(ledger)
    return ledger


@pytest.fixture
def setup_data(session: Session, ledger: Ledger):
    """Setup some accounts and transactions."""
    asset = Account(name="Assets", type=AccountType.ASSET, ledger_id=ledger.id, depth=1)
    cash = Account(name="Cash", type=AccountType.ASSET, ledger_id=ledger.id, parent=asset, depth=2)
    expense = Account(name="Expenses", type=AccountType.EXPENSE, ledger_id=ledger.id, depth=1)
    income = Account(name="Income", type=AccountType.INCOME, ledger_id=ledger.id, depth=1)
    salary = Account(
        name="Salary", type=AccountType.INCOME, ledger_id=ledger.id, parent=income, depth=2
    )

    session.add_all([asset, cash, expense, income, salary])
    session.commit()

    # Add an income transaction: Salary -> Cash (income credited, asset debited)
    tx = Transaction(
        ledger_id=ledger.id,
        date=date.today(),
        description="Salary Deposit",
        amount=Decimal("100.00"),
        from_account_id=salary.id,  # Income account (credit normal)
        to_account_id=cash.id,  # Asset account (debit normal)
        transaction_type=TransactionType.INCOME,
    )
    session.add(tx)
    session.commit()

    return {"cash": cash, "expense": expense, "income": income, "salary": salary}


def test_get_balance_sheet(client: TestClient, ledger: Ledger, setup_data):  # noqa: ARG001
    response = client.get(
        "/api/v1/reports/balance-sheet",
        params={"ledger_id": str(ledger.id), "date": date.today().isoformat()},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["date"] == date.today().isoformat()
    assert data["total_assets"] == "100.00"
    assert len(data["assets"]) > 0
    assert data["assets"][0]["name"] == "Assets"
    assert data["assets"][0]["children"][0]["name"] == "Cash"
    assert data["assets"][0]["children"][0]["amount"] == "100.00"


def test_get_balance_sheet_invalid_date(client: TestClient, ledger: Ledger):
    response = client.get(
        "/api/v1/reports/balance-sheet",
        params={"ledger_id": str(ledger.id), "date": "invalid-date"},
    )

    assert response.status_code == 422  # Validation error from Pydantic


def test_get_balance_sheet_future_date(client: TestClient, ledger: Ledger, setup_data):  # noqa: ARG001
    future_date = date.today() + timedelta(days=365)
    response = client.get(
        "/api/v1/reports/balance-sheet",
        params={"ledger_id": str(ledger.id), "date": future_date.isoformat()},
    )
    assert response.status_code == 200


def test_get_income_statement(client: TestClient, ledger: Ledger, setup_data):  # noqa: ARG001
    today = date.today()
    start_date = today.replace(day=1)
    end_date = today

    response = client.get(
        "/api/v1/reports/income-statement",
        params={
            "ledger_id": str(ledger.id),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()

    # We added an INCOME transaction in setup_data
    # 100.00 Income

    assert data["total_income"] == "100.00"
    assert data["total_expenses"] in ("0", "0.00")  # Zero can be formatted either way
    assert data["net_income"] == "100.00"
