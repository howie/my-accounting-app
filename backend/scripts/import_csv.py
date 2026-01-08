"""Import accounting data from CSV file.

This script imports accounts and transactions from a CSV file exported from
the legacy accounting system (MYAB format).

CSV Format:
- 日期: Date (YYYY/MM/DD)
- 分類: From Account (debit side)
- 科目: To Account (credit side)
- 金額: Amount
- 明細: Description
- 備註: Notes (optional)
- 發票: Invoice (optional)

Account Code Format:
- A- prefix: Asset (mapped to ASSET type, then stripped)
- L- prefix: Loans/借款 (mapped to LIABILITY type, then stripped)
- E- prefix: Expenses/支出 (mapped to EXPENSE type, then stripped)
- I- prefix: Income/收入 (mapped to INCOME type, then stripped)
- Equity: Special system account for initial balances

Hierarchy is indicated by '.' separator (after the type prefix):
- A-股票帳戶 → name="股票帳戶", type=ASSET, depth=1, parent=None
- A-股票帳戶.FirstTrade → name="FirstTrade", type=ASSET, depth=2, parent="A-股票帳戶"
- A-存款.國泰世華.主帳戶 → name="主帳戶", type=ASSET, depth=3, parent="A-存款.國泰世華"
"""

import csv
import decimal
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session, select

from src.db.session import engine
from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction, TransactionType
from src.models.user import User


@dataclass
class AccountInfo:
    """Parsed account information."""

    code: str
    name: str
    type: AccountType
    parent_code: str | None
    depth: int


@dataclass
class TransactionInfo:
    """Parsed transaction information."""

    date: datetime
    from_account_code: str
    to_account_code: str
    amount: Decimal
    description: str
    notes: str


def parse_account_type(code: str) -> AccountType:
    """Parse account type from code prefix."""
    if code.startswith("A-"):
        return AccountType.ASSET
    elif code.startswith("L-"):
        return AccountType.LIABILITY
    elif code.startswith("E-"):
        return AccountType.EXPENSE
    elif code.startswith("I-"):
        return AccountType.INCOME
    elif code == "Equity":
        # Equity is treated as Asset for initial balance transfers
        return AccountType.ASSET
    else:
        raise ValueError(f"Unknown account type prefix: {code}")


def strip_type_prefix(code: str) -> str:
    """Strip the type prefix (A-, L-, E-, I-) from account code.

    Examples:
        A-股票帳戶.FirstTrade -> 股票帳戶.FirstTrade
        E-生活開銷.餐飲 -> 生活開銷.餐飲
        Equity -> Equity (no prefix)
    """
    prefixes = ["A-", "L-", "E-", "I-"]
    for prefix in prefixes:
        if code.startswith(prefix):
            return code[len(prefix):]
    return code


def get_account_name(code: str) -> str:
    """Get the display name from account code (last segment after stripping prefix).

    Examples:
        A-股票帳戶.FirstTrade -> FirstTrade
        A-股票帳戶 -> 股票帳戶
        E-生活開銷.餐飲 -> 餐飲
    """
    # First strip the type prefix
    name_part = strip_type_prefix(code)
    # Then get the last segment
    parts = name_part.split(".")
    return parts[-1] if parts else name_part


def get_parent_code(code: str) -> str | None:
    """Get parent account code from hierarchical code."""
    parts = code.split(".")
    if len(parts) <= 1:
        return None
    return ".".join(parts[:-1])


def get_account_depth(code: str) -> int:
    """Calculate account depth from code.

    The depth is based on the hierarchy after stripping the type prefix.
    Examples:
        A-股票帳戶 -> depth 1 (root level)
        A-股票帳戶.FirstTrade -> depth 2 (child)
        A-股票帳戶.FirstTrade.子帳戶 -> depth 3 (grandchild)
        Equity -> depth 1 (root level, no prefix)
    """
    # Strip prefix and count hierarchy levels
    name_part = strip_type_prefix(code)
    return len(name_part.split("."))


def parse_accounts_from_csv(filepath: str) -> dict[str, AccountInfo]:
    """Parse all unique accounts from CSV file.

    Returns a dictionary of account code -> AccountInfo.
    Also creates intermediate parent accounts if they don't exist.
    """
    accounts: dict[str, AccountInfo] = {}

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Get both from and to account codes
            from_code = row["分類"].strip()
            to_code = row["科目"].strip()

            for code in [from_code, to_code]:
                if not code:
                    continue

                # Add the account itself
                if code not in accounts:
                    try:
                        account_type = parse_account_type(code)
                        parent_code = get_parent_code(code)
                        depth = get_account_depth(code)

                        accounts[code] = AccountInfo(
                            code=code,
                            name=get_account_name(code),
                            type=account_type,
                            parent_code=parent_code,
                            depth=depth,
                        )
                    except ValueError as e:
                        print(f"Warning: Skipping unknown account code: {code} - {e}")
                        continue

                # Add intermediate parent accounts
                parts = code.split(".")
                for i in range(1, len(parts)):
                    parent_code = ".".join(parts[:i])
                    if parent_code not in accounts:
                        try:
                            parent_type = parse_account_type(parent_code)
                            grandparent_code = get_parent_code(parent_code)
                            parent_depth = get_account_depth(parent_code)

                            accounts[parent_code] = AccountInfo(
                                code=parent_code,
                                name=get_account_name(parent_code),
                                type=parent_type,
                                parent_code=grandparent_code,
                                depth=parent_depth,
                            )
                        except ValueError:
                            continue

    return accounts


def parse_transactions_from_csv(filepath: str) -> list[TransactionInfo]:
    """Parse all transactions from CSV file.

    CSV columns mapping (based on MyAB conventions):
    The meaning of 分類/科目 columns varies by transaction type:
    - EXPENSE: 分類=to (expense category), 科目=from (payment source)
    - INCOME:  分類=from (income source), 科目=to (receiving account)
    - TRANSFER: 分類=to (destination), 科目=from (source)
    """
    transactions: list[TransactionInfo] = []

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row["日期"].strip()
            category = row["分類"].strip()  # 分類欄位
            account = row["科目"].strip()  # 科目欄位
            amount_str = row["金額"].strip()
            description = row["明細"].strip()
            notes = row.get("備註", "").strip()

            if not all([date_str, category, account, amount_str]):
                continue

            # Determine account types to figure out from/to mapping
            try:
                category_type = parse_account_type(category)
                account_type = parse_account_type(account)
            except ValueError:
                continue

            # Map from/to based on transaction type
            if category_type == AccountType.EXPENSE:
                # Expense: money flows FROM account TO expense category
                from_code = account  # A- or L- (payment source)
                to_code = category  # E- (expense type)
            elif category_type == AccountType.INCOME:
                # Income: money flows FROM income source TO account
                from_code = category  # I- (income source)
                to_code = account  # A- or L- (receiving account)
            else:
                # Transfer (both are Asset/Liability)
                # Convention: 分類=to (destination), 科目=from (source)
                from_code = account
                to_code = category

            try:
                # Parse date (YYYY/MM/DD format)
                date = datetime.strptime(date_str, "%Y/%m/%d").date()
                amount = Decimal(amount_str)

                if amount <= 0:
                    continue

                transactions.append(
                    TransactionInfo(
                        date=date,
                        from_account_code=from_code,
                        to_account_code=to_code,
                        amount=amount,
                        description=description,
                        notes=notes,
                    )
                )
            except (ValueError, decimal.InvalidOperation) as e:
                print(f"Warning: Skipping invalid row: {row} - {e}")
                continue

    return transactions


def determine_transaction_type(from_type: AccountType, to_type: AccountType) -> TransactionType:
    """Determine transaction type based on account types.

    Rules:
    - EXPENSE: from Asset/Liability, to Expense
    - INCOME: from Income, to Asset/Liability
    - TRANSFER: from Asset/Liability, to Asset/Liability
    """
    asset_liability = {AccountType.ASSET, AccountType.LIABILITY}

    if to_type == AccountType.EXPENSE:
        return TransactionType.EXPENSE
    elif from_type == AccountType.INCOME:
        return TransactionType.INCOME
    elif from_type in asset_liability and to_type in asset_liability:
        return TransactionType.TRANSFER
    else:
        # Default to TRANSFER for other cases
        return TransactionType.TRANSFER


def import_data(
    csv_filepath: str,
    user_email: str,
    ledger_name: str = "2025年度帳本",
    dry_run: bool = False,
) -> dict:
    """Import accounts and transactions from CSV.

    Args:
        csv_filepath: Path to the UTF-8 encoded CSV file
        user_email: Email of the user who owns the ledger
        ledger_name: Name for the new ledger
        dry_run: If True, don't commit changes

    Returns:
        Statistics about the import
    """
    stats = {
        "accounts_created": 0,
        "transactions_created": 0,
        "accounts_skipped": 0,
        "transactions_skipped": 0,
        "errors": [],
    }

    # Parse CSV
    print("Parsing CSV file...")
    account_infos = parse_accounts_from_csv(csv_filepath)
    transaction_infos = parse_transactions_from_csv(csv_filepath)

    print(f"Found {len(account_infos)} unique accounts")
    print(f"Found {len(transaction_infos)} transactions")

    with Session(engine) as session:
        # Get or create user
        user = session.exec(select(User).where(User.email == user_email)).first()

        if not user:
            raise ValueError(f"User with email '{user_email}' not found")

        print(f"Using user: {user.email} (ID: {user.id})")

        # Create ledger
        ledger = Ledger(
            user_id=user.id,
            name=ledger_name,
        )
        session.add(ledger)
        session.flush()  # Get ledger ID

        print(f"Created ledger: {ledger.name} (ID: {ledger.id})")

        # Create accounts in order (by depth, parents first)
        account_map: dict[str, uuid.UUID] = {}  # code -> account ID

        # Sort accounts by depth (ensure parents are created before children)
        sorted_accounts = sorted(account_infos.values(), key=lambda a: a.depth)

        for acc_info in sorted_accounts:
            # Get parent ID if exists
            parent_id = None
            if acc_info.parent_code and acc_info.parent_code in account_map:
                parent_id = account_map[acc_info.parent_code]

            # Create account
            # Use display name (last segment) for the account name
            # The hierarchy is maintained through parent_id relationships
            account = Account(
                ledger_id=ledger.id,
                name=acc_info.name,  # Use display name (last segment)
                type=acc_info.type,
                is_system=(acc_info.code == "Equity"),
                parent_id=parent_id,
                depth=min(acc_info.depth, 3),  # Cap at max depth 3
            )
            session.add(account)
            session.flush()

            account_map[acc_info.code] = account.id
            stats["accounts_created"] += 1

        print(f"Created {stats['accounts_created']} accounts")

        # Create transactions
        for tx_info in transaction_infos:
            from_account_id = account_map.get(tx_info.from_account_code)
            to_account_id = account_map.get(tx_info.to_account_code)

            if not from_account_id or not to_account_id:
                stats["transactions_skipped"] += 1
                stats["errors"].append(
                    f"Missing account for transaction: {tx_info.from_account_code} -> {tx_info.to_account_code}"
                )
                continue

            # Get account types to determine transaction type
            from_type = account_infos[tx_info.from_account_code].type
            to_type = account_infos[tx_info.to_account_code].type
            tx_type = determine_transaction_type(from_type, to_type)

            # Build description
            description = tx_info.description
            if tx_info.notes:
                description = f"{description} ({tx_info.notes})"

            transaction = Transaction(
                ledger_id=ledger.id,
                date=tx_info.date,
                description=description[:255],  # Truncate to max length
                amount=tx_info.amount,
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                transaction_type=tx_type,
            )
            session.add(transaction)
            stats["transactions_created"] += 1

        print(f"Created {stats['transactions_created']} transactions")

        if dry_run:
            print("DRY RUN - Rolling back changes")
            session.rollback()
        else:
            session.commit()
            print("Changes committed successfully")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Import accounting data from CSV")
    parser.add_argument(
        "csv_file",
        help="Path to the UTF-8 encoded CSV file",
    )
    parser.add_argument(
        "--user-email",
        required=True,
        help="Email of the user who will own the ledger",
    )
    parser.add_argument(
        "--ledger-name",
        default="2025年度帳本",
        help="Name for the new ledger (default: 2025年度帳本)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate without committing changes",
    )

    args = parser.parse_args()

    try:
        stats = import_data(
            csv_filepath=args.csv_file,
            user_email=args.user_email,
            ledger_name=args.ledger_name,
            dry_run=args.dry_run,
        )

        print("\n=== Import Summary ===")
        print(f"Accounts created: {stats['accounts_created']}")
        print(f"Transactions created: {stats['transactions_created']}")
        print(f"Accounts skipped: {stats['accounts_skipped']}")
        print(f"Transactions skipped: {stats['transactions_skipped']}")

        if stats["errors"]:
            print(f"\nErrors ({len(stats['errors'])}):")
            for error in stats["errors"][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(stats["errors"]) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
