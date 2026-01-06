import pytest
import sqlite3
from typing import List, Optional
from src.myab.persistence.database import get_db_connection
from src.myab.models.ledger import Ledger
from src.myab.models.account import Account
from src.myab.models.transaction import Transaction
from src.myab.services.ledger_service import LedgerService
from src.myab.services.account_service import AccountService
from src.myab.services.transaction_service import TransactionService
from src.myab.persistence.repositories.transaction_repository import TransactionRepository
from src.myab.validation.validators import TransactionValidator
from src.myab.persistence.repositories.account_repository import AccountRepository # Needed for TransactionValidator


def test_transaction_flow(ledger_service: LedgerService, account_service: AccountService, 
                          transaction_service: TransactionService, dummy_user_id: int, 
                          db_connection: sqlite3.Connection):
    
    user_account_id = dummy_user_id
    ledger_name = "Finance Ledger"
    initial_cash = 100000 # $1000.00 in cents

    # 1. Create a ledger and initial accounts
    ledger = ledger_service.create_ledger(user_account_id, ledger_name, initial_cash)
    
    accounts = account_service.list_accounts(ledger.id)
    cash_account = next(acc for acc in accounts if acc.name == "A-Cash")
    equity_account = next(acc for acc in accounts if acc.name == "Equity")

    # Create an expense account
    expense_account = account_service.create_account(ledger.id, "Food", "EXPENSE")
    
    # Create an income account
    income_account = account_service.create_account(ledger.id, "Salary", "INCOME")

    # Create a bank account
    bank_account = account_service.create_account(ledger.id, "Bank", "ASSET")


    # Verify initial balances (should be handled by a separate test/logic when transaction for initial cash is added)
    # For now, just ensure accounts exist

    # 2. Record an expense transaction
    expense_amount = 5000 # $50.00
    description = "Lunch at cafe"
    expense_transaction, msg = transaction_service.create_transaction(
        ledger.id, "2023-11-23", "EXPENSE", expense_amount,
        expense_account.id, cash_account.id, description
    )
    assert expense_transaction is not None, msg
    assert expense_transaction.amount == expense_amount

    # Verify account balances
    assert transaction_service.calculate_account_balance(cash_account.id) == (initial_cash - expense_amount) # This assumes initial cash is not from a transaction, or is 0
    assert transaction_service.calculate_account_balance(expense_account.id) == expense_amount
    
    # 3. Record an income transaction
    income_amount = 200000 # $2000.00
    income_transaction, msg = transaction_service.create_transaction(
        ledger.id, "2023-11-24", "INCOME", income_amount,
        cash_account.id, income_account.id, "Monthly Salary"
    )
    assert income_transaction is not None, msg
    assert transaction_service.calculate_account_balance(cash_account.id) == (initial_cash - expense_amount + income_amount)
    assert transaction_service.calculate_account_balance(income_account.id) == income_amount

    # 4. Record a transfer transaction
    transfer_amount = 100000 # $1000.00
    transfer_transaction, msg = transaction_service.create_transaction(
        ledger.id, "2023-11-25", "TRANSFER", transfer_amount,
        bank_account.id, cash_account.id, "Cash to Bank"
    )
    assert transfer_transaction is not None, msg
    assert transaction_service.calculate_account_balance(cash_account.id) == (initial_cash - expense_amount + income_amount - transfer_amount)
    assert transaction_service.calculate_account_balance(bank_account.id) == transfer_amount

    # 5. Update a transaction
    updated_description = "Updated Lunch at fancy cafe"
    expense_transaction.description = updated_description
    updated_success, msg = transaction_service.update_transaction(expense_transaction)
    assert updated_success is True, msg
    
    retrieved_expense_transaction = transaction_service.get_transaction(expense_transaction.id)
    assert retrieved_expense_transaction.description == updated_description

    # 6. Delete a transaction
    deleted_success, msg = transaction_service.delete_transaction(expense_transaction.id)
    assert deleted_success is True, msg
    deleted_transaction = transaction_service.get_transaction(expense_transaction.id)
    assert deleted_transaction is None

    # Verify final account balances after all operations
    assert transaction_service.calculate_account_balance(cash_account.id) == (initial_cash + income_amount - transfer_amount)
    assert transaction_service.calculate_account_balance(expense_account.id) == 0 # Since expense was deleted
    assert transaction_service.calculate_account_balance(income_account.id) == income_amount
    assert transaction_service.calculate_account_balance(bank_account.id) == transfer_amount
