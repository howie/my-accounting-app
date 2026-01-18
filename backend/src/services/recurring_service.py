from datetime import date
from uuid import UUID

from dateutil.relativedelta import relativedelta
from sqlmodel import Session, select

from src.models.advanced import Frequency, RecurringTransaction
from src.models.transaction import Transaction
from src.schemas.advanced import (
    RecurringTransactionCreate,
    RecurringTransactionDue,
    RecurringTransactionUpdate,
)


class RecurringService:
    def __init__(self, session: Session):
        self.session = session

    def create_recurring_transaction(
        self, data: RecurringTransactionCreate
    ) -> RecurringTransaction:
        rt = RecurringTransaction.model_validate(data)
        self.session.add(rt)
        self.session.commit()
        self.session.refresh(rt)
        return rt

    def list_recurring_transactions(self) -> list[RecurringTransaction]:
        return self.session.exec(select(RecurringTransaction)).all()

    def get_recurring_transaction(self, recurring_id: UUID) -> RecurringTransaction | None:
        return self.session.get(RecurringTransaction, recurring_id)

    def update_recurring_transaction(
        self, recurring_id: UUID, data: RecurringTransactionUpdate
    ) -> RecurringTransaction:
        rt = self.session.get(RecurringTransaction, recurring_id)
        if not rt:
            raise ValueError("Recurring Transaction not found")

        rt_data = data.model_dump(exclude_unset=True)
        for key, value in rt_data.items():
            setattr(rt, key, value)

        self.session.add(rt)
        self.session.commit()
        self.session.refresh(rt)
        return rt

    def delete_recurring_transaction(self, recurring_id: UUID) -> None:
        rt = self.session.get(RecurringTransaction, recurring_id)
        if not rt:
            raise ValueError("Recurring Transaction not found")
        self.session.delete(rt)
        self.session.commit()

    def _calculate_next_date(self, base_date: date, frequency: Frequency) -> date:
        if frequency == Frequency.DAILY:
            return base_date + relativedelta(days=1)
        elif frequency == Frequency.WEEKLY:
            return base_date + relativedelta(weeks=1)
        elif frequency == Frequency.MONTHLY:
            return base_date + relativedelta(months=1)
        elif frequency == Frequency.YEARLY:
            return base_date + relativedelta(years=1)
        return base_date  # Should not happen

    def get_due_transactions(self, check_date: date) -> list[RecurringTransactionDue]:
        # For MVP, we iterate and check (optimization: filter in DB if possible, but date math is hard in SQL)
        # Better: Select all active RecurringTransactions (end_date is null or >= check_date)
        # Then filter in python.

        query = select(RecurringTransaction)
        all_recurring = self.session.exec(query).all()

        due_list = []
        for rt in all_recurring:
            if rt.end_date and rt.end_date < check_date:
                continue

            next_due = rt.start_date
            if rt.last_generated_date:
                next_due = self._calculate_next_date(rt.last_generated_date, rt.frequency)

            # If start_date is in future relative to check_date, not due yet
            if next_due > check_date:
                continue

            # It is due
            due_list.append(
                RecurringTransactionDue(id=rt.id, name=rt.name, amount=rt.amount, due_date=next_due)
            )

        return due_list

    def approve_transaction(self, recurring_id: UUID, approval_date: date) -> Transaction:
        rt = self.session.get(RecurringTransaction, recurring_id)
        if not rt:
            raise ValueError("Recurring Transaction not found")

        # Create transaction
        # Need ledger_id from account. Since we have source/dest accounts,
        # we assume they are in the same ledger or we pick one.
        # Transaction model requires ledger_id.
        # Let's verify accounts exist and get ledger_id.
        # For simplicity, use source account's ledger.

        # Note: Transaction model fields: ledger_id, date, description, amount, from_account_id, to_account_id, transaction_type...

        # We need to fetch source account to get ledger_id
        from src.models.account import Account

        src_account = self.session.get(Account, rt.source_account_id)
        if not src_account:
            raise ValueError("Source account not found")

        new_txn = Transaction(
            ledger_id=src_account.ledger_id,
            date=approval_date,
            description=rt.name,
            amount=rt.amount,
            from_account_id=rt.source_account_id,
            to_account_id=rt.dest_account_id,
            transaction_type=rt.transaction_type,
            recurring_transaction_id=rt.id,
            notes=f"Generated from recurring transaction {rt.name}",
        )

        self.session.add(new_txn)

        # Update recurring record
        rt.last_generated_date = approval_date
        self.session.add(rt)

        self.session.commit()
        self.session.refresh(new_txn)
        return new_txn
