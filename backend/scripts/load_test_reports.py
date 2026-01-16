"""Load test for Reports.

Generates 30k transactions and measures report generation time.
"""

import asyncio
import time
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlmodel import Session, create_engine, select

from src.core.config import get_settings
from src.models import Account, AccountType, Ledger, Transaction, TransactionType, User
from src.services.report_service import ReportService

async def main():
    settings = get_settings()
    engine = create_engine(settings.database_url)

    with Session(engine) as session:
        # Create Test User & Ledger
        user = session.exec(select(User).where(User.email == "loadtest@example.com")).first()
        if not user:
            user = User(email="loadtest@example.com")
            session.add(user)
            session.commit()
            session.refresh(user)

        ledger = Ledger(name="Load Test Ledger", currency="USD", user_id=user.id)
        session.add(ledger)
        session.commit()
        session.refresh(ledger)

        print(f"Created Ledger: {ledger.id}")

        # Create Accounts
        asset = Account(name="Assets", type=AccountType.ASSET, ledger_id=ledger.id, depth=1)
        cash = Account(name="Cash", type=AccountType.ASSET, ledger_id=ledger.id, parent=asset, depth=2)
        income = Account(name="Income", type=AccountType.INCOME, ledger_id=ledger.id, depth=1)
        expense = Account(name="Expenses", type=AccountType.EXPENSE, ledger_id=ledger.id, depth=1)

        session.add_all([asset, cash, income, expense])
        session.commit()
        session.refresh(cash)
        session.refresh(income)
        session.refresh(expense)

        # Generate 30k Transactions
        print("Generating 30,000 transactions...")
        transactions = []
        start_date = date(2020, 1, 1)

        for i in range(30000):
            tx_date = start_date + timedelta(days=i % 1000)

            # Income: Income -> Cash
            transactions.append(Transaction(
                ledger_id=ledger.id,
                date=tx_date,
                description=f"Income {i}",
                amount=Decimal("100.00"),
                from_account_id=income.id,
                to_account_id=cash.id,
                transaction_type=TransactionType.INCOME
            ))

            # Expense: Cash -> Expense
            transactions.append(Transaction(
                ledger_id=ledger.id,
                date=tx_date,
                description=f"Expense {i}",
                amount=Decimal("50.00"),
                from_account_id=cash.id,
                to_account_id=expense.id,
                transaction_type=TransactionType.EXPENSE
            ))

            if len(transactions) >= 1000:
                session.add_all(transactions)
                session.commit()
                transactions = []
                print(f"Inserted {i+1}...")

        if transactions:
            session.add_all(transactions)
            session.commit()

        print("Data generation complete.")

        # Measure Report Generation Time
        service = ReportService(session)

        print("\n--- Benchmarking Balance Sheet ---")
        start_time = time.time()
        await service.get_balance_sheet(ledger.id, date.today())
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        print(f"Balance Sheet generation took: {duration:.2f} ms")
        if duration > 200:
            print("WARNING: Exceeded 200ms target!")
        else:
            print("SUCCESS: Within 200ms target.")

        print("\n--- Benchmarking Income Statement ---")
        start_time = time.time()
        await service.get_income_statement(ledger.id, date(2020, 1, 1), date.today())
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        print(f"Income Statement generation took: {duration:.2f} ms")

        # Cleanup
        # session.delete(ledger) # Cascade delete might be slow for 30k
        # session.commit()

if __name__ == "__main__":
    asyncio.run(main())
