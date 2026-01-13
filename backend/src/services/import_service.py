import uuid
from typing import TYPE_CHECKING, Any

from sqlmodel import Session

from src.models.account import Account
from src.models.transaction import Transaction
from src.schemas.data_import import (
    AccountMapping,
    AccountType,
    DuplicateWarning,
    ImportResult,
    ImportType,
    ParsedTransaction,
)
from src.services.csv_parser import MyAbCsvParser

if TYPE_CHECKING:
    from src.models.import_session import ImportSession


class ImportService:
    @staticmethod
    def find_duplicates(
        new_transactions: list[ParsedTransaction],
        existing_transactions: list[Transaction],
    ) -> list[DuplicateWarning]:
        """
        Find duplicate transactions based on date, amount, and accounts.
        Match criteria: Date + Amount + FromAccount + ToAccount.
        """
        duplicates: list[DuplicateWarning] = []

        # Build index for existing transactions
        # Key: (date, amount, from_acc_id, to_acc_id)
        existing_index: dict[tuple[Any, ...], list[Transaction]] = {}
        for tx in existing_transactions:
            key = (tx.date, tx.amount, tx.from_account_id, tx.to_account_id)
            if key not in existing_index:
                existing_index[key] = []
            existing_index[key].append(tx)

        for new_tx in new_transactions:
            # Only check if accounts are resolved
            if new_tx.from_account_id is None or new_tx.to_account_id is None:
                continue

            key = (new_tx.date, new_tx.amount, new_tx.from_account_id, new_tx.to_account_id)
            if key in existing_index:
                duplicates.append(
                    DuplicateWarning(
                        row_number=new_tx.row_number,
                        existing_transaction_ids=[tx.id for tx in existing_index[key]],
                        similarity_reason="同日期+同金額+同科目",
                    )
                )

        return duplicates

    @staticmethod
    def auto_map_accounts(
        transactions: list[ParsedTransaction],
        existing_accounts: list[Account],
        import_type: ImportType,
    ) -> tuple[list[ParsedTransaction], list[AccountMapping]]:
        """
        Auto-map transactions to existing accounts by name.
        """
        # Extract unique account names involved
        account_names: dict[str, AccountType | None] = {}

        for tx in transactions:
            # We need to guess type for the account name
            # Only needed for AccountMapping creation (csv_account_type)

            # From Name
            if tx.from_account_name not in account_names:
                ac_type = None
                if import_type == ImportType.MYAB_CSV:
                    ac_type = MyAbCsvParser.parse_account_prefix(tx.from_account_name)
                    if not ac_type:
                        ac_type = AccountType.ASSET  # Default fallback
                elif import_type == ImportType.CREDIT_CARD:
                    ac_type = AccountType.LIABILITY
                else:
                    ac_type = AccountType.ASSET

                account_names[tx.from_account_name] = ac_type

            # To Name
            if tx.to_account_name not in account_names:
                ac_type = None
                if import_type == ImportType.MYAB_CSV:
                    ac_type = MyAbCsvParser.parse_account_prefix(tx.to_account_name)
                    if not ac_type:
                        ac_type = AccountType.EXPENSE  # Default fallback
                elif import_type == ImportType.CREDIT_CARD:
                    # To account for credit card is expense category
                    ac_type = AccountType.EXPENSE
                else:
                    ac_type = AccountType.EXPENSE

                account_names[tx.to_account_name] = ac_type

        # Index existing accounts by name for quick lookup
        existing_index: dict[str, Account] = {a.name: a for a in existing_accounts}

        mappings: list[AccountMapping] = []
        name_to_id: dict[str, uuid.UUID] = {}

        for name, ac_type in account_names.items():
            system_account = existing_index.get(name)
            system_id = system_account.id if system_account else None

            # Try stripping prefix for MyAB if no exact match
            suggested_name = name
            if import_type == ImportType.MYAB_CSV and not system_id and "-" in name:
                parts = name.split("-", 1)
                if len(parts) == 2:
                    stripped = parts[1]
                # Check if stripped name exists
                potential_account = existing_index.get(stripped)
                if potential_account:
                    system_id = potential_account.id
                    suggested_name = stripped

            mappings.append(
                AccountMapping(
                    csv_account_name=name,
                    csv_account_type=ac_type if ac_type else AccountType.EXPENSE,
                    system_account_id=system_id,
                    create_new=not system_id,
                    suggested_name=suggested_name,
                )
            )

            if system_id:
                name_to_id[name] = system_id

        # Update transactions
        for tx in transactions:
            if tx.from_account_name in name_to_id:
                tx.from_account_id = name_to_id[tx.from_account_name]
            if tx.to_account_name in name_to_id:
                tx.to_account_id = name_to_id[tx.to_account_name]

        return transactions, mappings

    @staticmethod
    def execute_import(
        session: "Session",
        import_session: "ImportSession",
        transactions: list[ParsedTransaction],
        mappings: list[AccountMapping],
        skip_rows: list[int],
    ) -> "ImportResult":
        from datetime import datetime

        from src.models.import_session import ImportStatus
        from src.schemas.data_import import CreatedAccount

        # 1. Process Mappings & Create Accounts
        name_to_id = {}
        created_accounts_list = []

        # Load Ledger to get owner_id
        # import_session might differ from session state, reload to be sure or use relation
        # We assume import_session is attached to session
        # If not loaded, we might need to fetch ledger.
        # But import_session.ledger_id is available.
        # We need user_id for Transaction.owner_id.
        # Transaction model: owner_id: uuid.UUID = Field(foreign_key="users.id")
        # We can fetch ledger owner.

        # Avoid circular import if needed, but imported inside method is fine.
        from src.models.ledger import Ledger

        ledger = session.get(Ledger, import_session.ledger_id)
        if not ledger:
            raise ValueError("Ledger not found")
        owner_id = ledger.user_id

        for m in mappings:
            # Map by CSV name
            if m.system_account_id:
                name_to_id[m.csv_account_name] = m.system_account_id
            elif m.create_new:
                # Create Account
                new_acc = Account(
                    name=m.suggested_name or m.csv_account_name,
                    type=m.csv_account_type,
                    ledger_id=import_session.ledger_id,
                )
                session.add(new_acc)
                session.flush()  # Get ID
                session.refresh(new_acc)
                name_to_id[m.csv_account_name] = new_acc.id

                created_accounts_list.append(
                    CreatedAccount(id=new_acc.id, name=new_acc.name, type=new_acc.type)
                )

        # 2. Process Transactions
        imported_count = 0
        skipped_count = 0

        for tx in transactions:
            if tx.row_number in skip_rows:
                skipped_count += 1
                continue

            # Resolve IDs using Mappings
            from_id = name_to_id.get(tx.from_account_name)
            to_id = name_to_id.get(tx.to_account_name)

            if not from_id or not to_id:
                # If mapping not explicit, check if we Auto-mapped earlier in Preview?
                # Preview returned mappings. User might have modified.
                # Request `mappings` should contain all involved accounts.
                # If missing, it's an error.
                raise ValueError(
                    f"Account mapping missing for account '{tx.from_account_name}' or '{tx.to_account_name}' in row {tx.row_number}"
                )

            # Create Transaction
            db_tx = Transaction(
                ledger_id=import_session.ledger_id,
                date=tx.date,
                amount=tx.amount,
                description=tx.description,
                from_account_id=from_id,
                to_account_id=to_id,
                owner_id=owner_id,
            )
            session.add(db_tx)
            imported_count += 1

        # 3. Update Import Session
        import_session.status = ImportStatus.COMPLETED
        import_session.imported_count = imported_count
        import_session.skipped_count = skipped_count
        import_session.created_accounts_count = len(created_accounts_list)
        import_session.completed_at = datetime.now()

        session.add(import_session)

        # 4. Create Audit Log
        from src.models.audit_log import AuditAction, AuditLog

        audit_log = AuditLog(
            ledger_id=import_session.ledger_id,
            entity_type="ImportSession",
            entity_id=import_session.id,
            action=AuditAction.CREATE,
            extra_data={
                "message": f"Imported {imported_count} transactions from {import_session.source_filename}",
                "imported_count": imported_count,
                "created_accounts_count": len(created_accounts_list),
            },
        )
        session.add(audit_log)

        return ImportResult(
            success=True,
            imported_count=imported_count,
            skipped_count=skipped_count,
            created_accounts=created_accounts_list,
        )
