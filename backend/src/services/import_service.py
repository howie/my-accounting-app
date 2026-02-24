import uuid
from typing import TYPE_CHECKING, Any

from sqlmodel import Session

from src.models.account import Account
from src.models.transaction import Transaction
from src.schemas.data_import import (
    AccountMapping,
    CreatedAccount,
    DuplicateWarning,
    ImportResult,
    ParsedAccountPath,
    ParsedTransaction,
    TransactionOverride,
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
    def _build_account_hierarchy_index(
        accounts: list[Account],
    ) -> dict[str, Account]:
        """
        Build an index mapping full hierarchical paths to accounts.

        Example: If we have accounts:
        - "信用卡" (id=1, parent=None)
        - "國泰世華信用卡" (id=2, parent=1)
        - "Cube卡" (id=3, parent=2)

        The index will contain:
        - "信用卡" -> Account(id=1)
        - "信用卡.國泰世華信用卡" -> Account(id=2)
        - "信用卡.國泰世華信用卡.Cube卡" -> Account(id=3)
        """
        # First, build parent lookup
        id_to_account: dict[uuid.UUID, Account] = {a.id: a for a in accounts}

        def get_full_path(account: Account) -> str:
            """Recursively build full path for an account."""
            path_parts = [account.name]
            current = account
            while current.parent_id:
                parent = id_to_account.get(current.parent_id)
                if parent:
                    path_parts.insert(0, parent.name)
                    current = parent
                else:
                    break
            return ".".join(path_parts)

        # Build index
        path_index: dict[str, Account] = {}
        for account in accounts:
            full_path = get_full_path(account)
            path_index[full_path] = account

        return path_index

    @staticmethod
    def auto_map_accounts(
        transactions: list[ParsedTransaction],
        existing_accounts: list[Account],
    ) -> tuple[list[ParsedTransaction], list[AccountMapping]]:
        """
        Auto-map transactions to existing accounts by hierarchical path.

        For MyAB CSV imports, accounts are matched by their full hierarchical path.
        Example: "L-信用卡.國泰世華信用卡.Cube卡" matches the leaf account "Cube卡"
        under "國泰世華信用卡" under "信用卡".
        """
        # Build hierarchical path index for existing accounts
        path_index = ImportService._build_account_hierarchy_index(existing_accounts)

        # Also index by simple name for fallback
        name_index: dict[str, Account] = {a.name: a for a in existing_accounts}

        # Extract unique account paths involved
        account_paths: dict[str, ParsedAccountPath] = {}

        for tx in transactions:
            # From account
            if tx.from_account_name not in account_paths:
                if tx.from_account_path:
                    account_paths[tx.from_account_name] = tx.from_account_path
                else:
                    # Fallback: parse from name
                    account_paths[tx.from_account_name] = MyAbCsvParser.parse_hierarchical_account(
                        tx.from_account_name
                    )

            # To account
            if tx.to_account_name not in account_paths:
                if tx.to_account_path:
                    account_paths[tx.to_account_name] = tx.to_account_path
                else:
                    # Fallback: parse from name
                    account_paths[tx.to_account_name] = MyAbCsvParser.parse_hierarchical_account(
                        tx.to_account_name
                    )

        mappings: list[AccountMapping] = []
        name_to_id: dict[str, uuid.UUID] = {}

        for raw_name, parsed_path in account_paths.items():
            system_id: uuid.UUID | None = None

            # Try to match by full hierarchical path
            full_path = parsed_path.full_path
            if full_path in path_index:
                system_id = path_index[full_path].id
            else:
                # Try matching by leaf name only (for backward compatibility)
                leaf_name = parsed_path.leaf_name
                if leaf_name in name_index:
                    # Verify the type matches
                    existing = name_index[leaf_name]
                    if existing.type.value == parsed_path.account_type.value:
                        system_id = existing.id

            mappings.append(
                AccountMapping(
                    csv_account_name=raw_name,
                    csv_account_type=parsed_path.account_type,
                    path_segments=parsed_path.path_segments,
                    system_account_id=system_id,
                    create_new=system_id is None,
                    suggested_name=parsed_path.leaf_name,
                )
            )

            if system_id:
                name_to_id[raw_name] = system_id

        # Update transactions with resolved IDs
        for tx in transactions:
            if tx.from_account_name in name_to_id:
                tx.from_account_id = name_to_id[tx.from_account_name]
            if tx.to_account_name in name_to_id:
                tx.to_account_id = name_to_id[tx.to_account_name]

        return transactions, mappings

    @staticmethod
    def _create_hierarchical_accounts(
        session: "Session",
        ledger_id: uuid.UUID,
        mappings: list[AccountMapping],
        existing_accounts: list[Account],
    ) -> tuple[dict[str, uuid.UUID], list[CreatedAccount]]:
        """
        Create hierarchical accounts from mappings.

        This method creates accounts in the correct order (parents before children)
        and properly sets parent_id and depth for each account.

        Returns:
            Tuple of (name_to_id mapping, list of created accounts)
        """

        name_to_id: dict[str, uuid.UUID] = {}
        created_accounts_list: list[CreatedAccount] = []

        # Build existing account index by (name, parent_id, type)
        # This helps us find or create accounts at each level
        existing_by_name_parent: dict[tuple[str, uuid.UUID | None, str], Account] = {}
        for acc in existing_accounts:
            key = (acc.name, acc.parent_id, acc.type.value)
            existing_by_name_parent[key] = acc

        # Also build path index for quick lookups
        path_index = ImportService._build_account_hierarchy_index(existing_accounts)

        # Track accounts we've created in this import (path -> account_id)
        created_path_to_id: dict[str, uuid.UUID] = {}

        # Process mappings that need new accounts
        for m in mappings:
            if m.system_account_id:
                # Already mapped to existing account
                name_to_id[m.csv_account_name] = m.system_account_id
                continue

            if not m.create_new:
                continue

            # Need to create account(s) for this path
            path_segments = (
                m.path_segments if m.path_segments else [m.suggested_name or m.csv_account_name]
            )
            account_type = m.csv_account_type

            # Create accounts for each level in the path
            current_parent_id: uuid.UUID | None = None
            current_path_parts: list[str] = []

            for depth_idx, segment_name in enumerate(path_segments):
                current_path_parts.append(segment_name)
                current_path = ".".join(current_path_parts)
                depth = depth_idx + 1  # 1-indexed depth

                # Check if this path already exists in DB or was created in this import
                if current_path in path_index:
                    # Already exists in DB
                    existing_acc = path_index[current_path]
                    current_parent_id = existing_acc.id
                    continue

                if current_path in created_path_to_id:
                    # Already created in this import
                    current_parent_id = created_path_to_id[current_path]
                    continue

                # Need to create this account
                new_acc = Account(
                    name=segment_name,
                    type=account_type,
                    ledger_id=ledger_id,
                    parent_id=current_parent_id,
                    depth=depth,
                )
                session.add(new_acc)
                session.flush()  # Get ID
                session.refresh(new_acc)

                # Track the created account
                created_path_to_id[current_path] = new_acc.id
                current_parent_id = new_acc.id

                # Only add leaf accounts to created_accounts_list for reporting
                is_leaf = depth_idx == len(path_segments) - 1
                if is_leaf:
                    created_accounts_list.append(
                        CreatedAccount(id=new_acc.id, name=new_acc.name, type=new_acc.type)
                    )

            # Map the original CSV name to the leaf account ID
            if current_parent_id:
                name_to_id[m.csv_account_name] = current_parent_id

        return name_to_id, created_accounts_list

    @staticmethod
    def execute_import(
        session: "Session",
        import_session: "ImportSession",
        transactions: list[ParsedTransaction],
        mappings: list[AccountMapping],
        skip_rows: list[int],
        transaction_overrides: dict[int, TransactionOverride] | None = None,
    ) -> "ImportResult":
        from datetime import datetime

        from sqlmodel import select

        from src.models.import_session import ImportStatus
        from src.models.ledger import Ledger

        # Verify ledger exists
        ledger = session.get(Ledger, import_session.ledger_id)
        if not ledger:
            raise ValueError("Ledger not found")

        # Load existing accounts for hierarchical creation
        existing_accounts = list(
            session.exec(select(Account).where(Account.ledger_id == import_session.ledger_id)).all()
        )

        # 1. Process Mappings & Create Hierarchical Accounts
        name_to_id, created_accounts_list = ImportService._create_hierarchical_accounts(
            session=session,
            ledger_id=import_session.ledger_id,
            mappings=mappings,
            existing_accounts=existing_accounts,
        )

        # Add existing mappings to name_to_id
        for m in mappings:
            if m.system_account_id and m.csv_account_name not in name_to_id:
                name_to_id[m.csv_account_name] = m.system_account_id

        # 2. Process Transactions
        imported_count = 0
        skipped_count = 0
        overrides = transaction_overrides or {}

        for tx in transactions:
            if tx.row_number in skip_rows:
                skipped_count += 1
                continue

            override = overrides.get(tx.row_number)

            # Resolve IDs: override takes priority over name_to_id lookup
            from_id = (
                override.from_account_id
                if override and override.from_account_id
                else name_to_id.get(tx.from_account_name)
            )
            to_id = (
                override.to_account_id
                if override and override.to_account_id
                else name_to_id.get(tx.to_account_name)
            )

            if not from_id or not to_id:
                raise ValueError(
                    f"Account mapping missing for account '{tx.from_account_name}' or '{tx.to_account_name}' in row {tx.row_number}"
                )

            # Create Transaction
            # Convert schema TransactionType to model TransactionType
            from src.models.transaction import TransactionType as ModelTransactionType

            model_tx_type = ModelTransactionType(tx.transaction_type.value)

            db_tx = Transaction(
                ledger_id=import_session.ledger_id,
                date=override.date if override and override.date else tx.date,
                amount=override.amount if override and override.amount is not None else tx.amount,
                description=(
                    override.description
                    if override and override.description is not None
                    else tx.description
                ),
                from_account_id=from_id,
                to_account_id=to_id,
                transaction_type=model_tx_type,
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
