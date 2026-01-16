from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.models.account import Account
from src.models.transaction import Transaction, TransactionType
from src.services.export_service import ExportService


@pytest.fixture
def mock_session():
    return Mock()


@pytest.fixture
def export_service(mock_session):
    return ExportService(mock_session)


@pytest.fixture
def sample_transactions():
    # Setup accounts
    acc_cash = Mock(spec=Account)
    acc_cash.name = "Cash"

    acc_food = Mock(spec=Account)
    acc_food.name = "Food"

    acc_salary = Mock(spec=Account)
    acc_salary.name = "Salary"

    acc_bank = Mock(spec=Account)
    acc_bank.name = "Bank"

    # Expense: Cash -> Food
    t1 = Transaction(
        id=uuid4(),
        ledger_id=uuid4(),
        date=date(2024, 1, 1),
        transaction_type=TransactionType.EXPENSE,
        amount=Decimal("100.50"),
        description="Lunch",
        from_account_id=uuid4(),
        to_account_id=uuid4(),
    )
    t1.from_account = acc_cash
    t1.to_account = acc_food

    # Income: Salary -> Bank
    t2 = Transaction(
        id=uuid4(),
        ledger_id=uuid4(),
        date=date(2024, 1, 5),
        transaction_type=TransactionType.INCOME,
        amount=Decimal("5000.00"),
        description="Paycheck",
        from_account_id=uuid4(),
        to_account_id=uuid4(),
    )
    t2.from_account = acc_salary
    t2.to_account = acc_bank

    # Transfer: Cash -> Bank
    t3 = Transaction(
        id=uuid4(),
        ledger_id=uuid4(),
        date=date(2024, 1, 10),
        transaction_type=TransactionType.TRANSFER,
        amount=Decimal("200.00"),
        description="Deposit",
        from_account_id=uuid4(),
        to_account_id=uuid4(),
    )
    t3.from_account = acc_cash
    t3.to_account = acc_bank

    return [t1, t2, t3]


def test_generate_csv_content_success(export_service, sample_transactions):
    generator = export_service.generate_csv_content(sample_transactions)
    content = list(generator)

    # Check BOM
    assert content[0] == "\ufeff"

    # Check Header
    full_csv = "".join(content[1:])  # Skip BOM
    lines = full_csv.strip().split("\r\n")
    # Python csv writer uses \r\n by default on many platforms or just \n depending on config, let's split safely
    if len(lines) == 1:  # Maybe just \n
        lines = full_csv.strip().split("\n")

    assert "日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼" in lines[0]

    # Check Expense Row
    # Date, Type, Expense, Income, From, To, Amount, Desc, Inv
    # 2024-01-01,支出,Food,,Cash,,100.50,Lunch,
    assert "2024-01-01,支出,Food,,Cash,,100.50,Lunch," in lines[1]

    # Check Income Row
    # 2024-01-05,收入,,Salary,,Bank,5000.00,Paycheck,
    assert "2024-01-05,收入,,Salary,,Bank,5000.00,Paycheck," in lines[2]

    # Check Transfer Row
    # 2024-01-10,轉帳,,,Cash,Bank,200.00,Deposit,
    assert "2024-01-10,轉帳,,,Cash,Bank,200.00,Deposit," in lines[3]


def test_generate_html_content_success(export_service, sample_transactions):
    html_content = export_service.generate_html_content(
        sample_transactions, "2024-01-01 to 2024-01-31"
    )

    # Check basic structure
    assert "<!DOCTYPE html>" in html_content
    assert "Transaction Report" in html_content

    # Check Metadata
    assert "2024-01-01 to 2024-01-31" in html_content

    # Check Transaction Data presence
    # T1: Expense 100.50
    assert "100.50" in html_content
    assert "Lunch" in html_content
    assert "Expense" in html_content

    # T2: Income 5000.00
    assert "5,000.00" in html_content  # Formatting check
    assert "Paycheck" in html_content

    # T3: Transfer 200.00
    assert "200.00" in html_content
    assert "Deposit" in html_content
