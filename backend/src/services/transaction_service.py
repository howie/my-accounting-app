"""Transaction service for business logic.

Based on contracts/transaction_service.md
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlmodel import Session, select, or_

from src.models.account import Account, AccountType
from src.models.transaction import Transaction, TransactionType
from src.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionRead,
    TransactionListItem,
    PaginatedTransactions,
    AccountSummary,
)


class TransactionService:
    """Service for managing transactions within a ledger.

    Handles transaction CRUD operations with validation for
    double-entry bookkeeping rules.
    """

    def __init__(self, session: Session) -> None:
        """Initialize service with database session."""
        self.session = session

    def create_transaction(
        self, ledger_id: uuid.UUID, data: TransactionCreate
    ) -> Transaction:
        """Create a new transaction.

        Validates:
        - from_account and to_account are different
        - Both accounts exist and belong to the ledger
        - Account types are valid for the transaction type
        - Amount is positive
        - Description is not empty
        """
        # Validate accounts are different
        if data.from_account_id == data.to_account_id:
            raise ValueError("Cannot create transaction with same account for from and to")

        # Get both accounts
        from_account = self._get_account(data.from_account_id, ledger_id)
        to_account = self._get_account(data.to_account_id, ledger_id)

        # Validate account types for transaction type
        self._validate_account_types(
            data.transaction_type, from_account, to_account
        )

        # Create transaction
        transaction = Transaction(
            ledger_id=ledger_id,
            date=data.date,
            description=data.description,
            amount=data.amount,
            from_account_id=data.from_account_id,
            to_account_id=data.to_account_id,
            transaction_type=data.transaction_type,
        )

        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction

    def get_transactions(
        self,
        ledger_id: uuid.UUID,
        limit: int = 50,
        cursor: str | None = None,
        search: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        account_id: uuid.UUID | None = None,
        transaction_type: TransactionType | None = None,
    ) -> PaginatedTransactions:
        """Get paginated list of transactions for a ledger with optional filters.

        Args:
            ledger_id: The ledger to get transactions from
            limit: Maximum number of transactions to return (default 50)
            cursor: Cursor for pagination (transaction ID)
            search: Case-insensitive search term for description
            from_date: Filter transactions on or after this date
            to_date: Filter transactions on or before this date
            account_id: Filter transactions involving this account (from or to)
            transaction_type: Filter by transaction type (EXPENSE, INCOME, TRANSFER)

        Returns transactions in descending order by date, then created_at.
        """
        statement = (
            select(Transaction)
            .where(Transaction.ledger_id == ledger_id)
        )

        # Apply search filter (case-insensitive description search)
        if search and search.strip():
            search_term = f"%{search.strip().lower()}%"
            statement = statement.where(
                Transaction.description.ilike(search_term)
            )

        # Apply date filters
        if from_date:
            statement = statement.where(Transaction.date >= from_date)

        if to_date:
            statement = statement.where(Transaction.date <= to_date)

        # Apply account filter (matches from_account OR to_account)
        if account_id:
            statement = statement.where(
                or_(
                    Transaction.from_account_id == account_id,
                    Transaction.to_account_id == account_id,
                )
            )

        # Apply transaction type filter
        if transaction_type:
            statement = statement.where(
                Transaction.transaction_type == transaction_type
            )

        # Apply ordering
        statement = statement.order_by(
            Transaction.date.desc(), Transaction.created_at.desc()
        )

        # Apply cursor for pagination
        if cursor:
            try:
                cursor_uuid = uuid.UUID(cursor)
                cursor_tx = self.session.get(Transaction, cursor_uuid)
                if cursor_tx:
                    statement = statement.where(
                        or_(
                            Transaction.date < cursor_tx.date,
                            (
                                (Transaction.date == cursor_tx.date)
                                & (Transaction.created_at < cursor_tx.created_at)
                            ),
                        )
                    )
            except ValueError:
                pass  # Invalid cursor, ignore

        # Apply limit (fetch one extra to determine has_more)
        statement = statement.limit(limit + 1)

        result = list(self.session.exec(statement).all())

        has_more = len(result) > limit
        if has_more:
            result = result[:limit]

        items = []
        for tx in result:
            # Eager load accounts
            from_account = self.session.get(Account, tx.from_account_id)
            to_account = self.session.get(Account, tx.to_account_id)

            items.append(
                TransactionListItem(
                    id=tx.id,
                    date=tx.date,
                    description=tx.description,
                    amount=tx.amount,
                    transaction_type=tx.transaction_type,
                    from_account=AccountSummary(
                        id=from_account.id,
                        name=from_account.name,
                        type=from_account.type,
                    ),
                    to_account=AccountSummary(
                        id=to_account.id,
                        name=to_account.name,
                        type=to_account.type,
                    ),
                )
            )

        next_cursor = str(result[-1].id) if result and has_more else None

        return PaginatedTransactions(
            data=items,
            cursor=next_cursor,
            has_more=has_more,
        )

    def get_transaction(
        self, transaction_id: uuid.UUID, ledger_id: uuid.UUID
    ) -> TransactionRead | None:
        """Get a single transaction by ID."""
        statement = select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.ledger_id == ledger_id,
        )
        transaction = self.session.exec(statement).first()

        if not transaction:
            return None

        # Load accounts
        from_account = self.session.get(Account, transaction.from_account_id)
        to_account = self.session.get(Account, transaction.to_account_id)

        return TransactionRead(
            id=transaction.id,
            ledger_id=transaction.ledger_id,
            date=transaction.date,
            description=transaction.description,
            amount=transaction.amount,
            from_account_id=transaction.from_account_id,
            to_account_id=transaction.to_account_id,
            transaction_type=transaction.transaction_type,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
            from_account=AccountSummary(
                id=from_account.id,
                name=from_account.name,
                type=from_account.type,
            ) if from_account else None,
            to_account=AccountSummary(
                id=to_account.id,
                name=to_account.name,
                type=to_account.type,
            ) if to_account else None,
        )

    def update_transaction(
        self,
        transaction_id: uuid.UUID,
        ledger_id: uuid.UUID,
        data: TransactionUpdate,
    ) -> TransactionRead | None:
        """Update an existing transaction.

        All fields must be provided (full replacement).
        Same validation rules as create.
        """
        transaction = self.session.exec(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.ledger_id == ledger_id,
            )
        ).first()

        if not transaction:
            return None

        # Validate accounts are different
        if data.from_account_id == data.to_account_id:
            raise ValueError("Cannot update transaction with same account for from and to")

        # Get both accounts
        from_account = self._get_account(data.from_account_id, ledger_id)
        to_account = self._get_account(data.to_account_id, ledger_id)

        # Validate account types
        self._validate_account_types(
            data.transaction_type, from_account, to_account
        )

        # Update fields
        transaction.date = data.date
        transaction.description = data.description
        transaction.amount = data.amount
        transaction.from_account_id = data.from_account_id
        transaction.to_account_id = data.to_account_id
        transaction.transaction_type = data.transaction_type
        transaction.updated_at = datetime.now(timezone.utc)

        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)

        return TransactionRead(
            id=transaction.id,
            ledger_id=transaction.ledger_id,
            date=transaction.date,
            description=transaction.description,
            amount=transaction.amount,
            from_account_id=transaction.from_account_id,
            to_account_id=transaction.to_account_id,
            transaction_type=transaction.transaction_type,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
            from_account=AccountSummary(
                id=from_account.id,
                name=from_account.name,
                type=from_account.type,
            ),
            to_account=AccountSummary(
                id=to_account.id,
                name=to_account.name,
                type=to_account.type,
            ),
        )

    def delete_transaction(
        self, transaction_id: uuid.UUID, ledger_id: uuid.UUID
    ) -> bool:
        """Delete a transaction.

        Returns True if deleted, False if not found.
        """
        transaction = self.session.exec(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.ledger_id == ledger_id,
            )
        ).first()

        if not transaction:
            return False

        self.session.delete(transaction)
        self.session.commit()
        return True

    def _get_account(self, account_id: uuid.UUID, ledger_id: uuid.UUID) -> Account:
        """Get an account and validate it belongs to the ledger.

        Raises ValueError if account not found or belongs to different ledger.
        """
        account = self.session.get(Account, account_id)

        if not account:
            raise ValueError(f"Account {account_id} not found")

        if account.ledger_id != ledger_id:
            raise ValueError(
                f"Account {account_id} does not belong to ledger {ledger_id}"
            )

        return account

    def _validate_account_types(
        self,
        transaction_type: TransactionType,
        from_account: Account,
        to_account: Account,
    ) -> None:
        """Validate account types are valid for the transaction type.

        Rules:
        - EXPENSE: from Asset/Liability, to Expense
        - INCOME: from Income, to Asset/Liability
        - TRANSFER: from Asset/Liability, to Asset/Liability
        """
        asset_liability = {AccountType.ASSET, AccountType.LIABILITY}

        if transaction_type == TransactionType.EXPENSE:
            if from_account.type not in asset_liability:
                raise ValueError(
                    f"EXPENSE transaction from_account must be Asset or Liability, "
                    f"got {from_account.type}"
                )
            if to_account.type != AccountType.EXPENSE:
                raise ValueError(
                    f"EXPENSE transaction to_account must be Expense, "
                    f"got {to_account.type}"
                )

        elif transaction_type == TransactionType.INCOME:
            if from_account.type != AccountType.INCOME:
                raise ValueError(
                    f"INCOME transaction from_account must be Income, "
                    f"got {from_account.type}"
                )
            if to_account.type not in asset_liability:
                raise ValueError(
                    f"INCOME transaction to_account must be Asset or Liability, "
                    f"got {to_account.type}"
                )

        elif transaction_type == TransactionType.TRANSFER:
            if from_account.type not in asset_liability:
                raise ValueError(
                    f"TRANSFER transaction from_account must be Asset or Liability, "
                    f"got {from_account.type}"
                )
            if to_account.type not in asset_liability:
                raise ValueError(
                    f"TRANSFER transaction to_account must be Asset or Liability, "
                    f"got {to_account.type}"
                )
