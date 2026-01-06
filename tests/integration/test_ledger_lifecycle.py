import pytest
import os
from pathlib import Path
import sqlite3
from src.myab.persistence.database import initialize_database, get_db_connection
from src.myab.models.ledger import Ledger
from src.myab.models.account import Account
from src.myab.services.ledger_service import LedgerService
from src.myab.services.account_service import AccountService
from src.myab.persistence.repositories.ledger_repository import LedgerRepository
from src.myab.persistence.repositories.account_repository import AccountRepository


def test_ledger_creation_lifecycle(ledger_service: LedgerService, account_repository: AccountRepository, dummy_user_id: int):
    """
    Tests the complete lifecycle of ledger creation using actual services and repositories:
    - Ledger is created in the database.
    - Initial 'Cash' and 'Equity' accounts are created for the new ledger.
    - Initial cash amount is reflected (implicitly, through initial accounts).
    """
    user_account_id = dummy_user_id
    ledger_name = "My Test Ledger"
    initial_cash_amount = 5000.0

    # 1. Create a ledger using the service
    created_ledger = ledger_service.create_ledger(user_account_id, ledger_name, initial_cash_amount)

    assert created_ledger is not None
    assert created_ledger.name == ledger_name
    assert created_ledger.user_account_id == user_account_id
    assert created_ledger.id is not None

    # 2. Verify initial accounts exist for this ledger using the account repository
    accounts_data = account_repository.get_by_ledger_id(created_ledger.id)
    assert len(accounts_data) == 2

    cash_found = False
    equity_found = False
    for acc in accounts_data:
        if acc.name == "A-Cash" and acc.type == "ASSET" and acc.is_predefined == 1:
            cash_found = True
        if acc.name == "Equity" and acc.type == "EQUITY" and acc.is_predefined == 1:
            equity_found = True
    
    assert cash_found
    assert equity_found

    # TODO: Further verification (once transaction service is available):
    # - Verify that an initial transaction is created between Cash and Equity for initial_cash_amount
