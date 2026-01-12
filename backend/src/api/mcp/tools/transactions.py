"""MCP tools for transaction operations.

Based on contracts/mcp-tools.md from 007-api-for-mcp feature.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Any

from sqlmodel import Session, select

from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction, TransactionType
from src.models.user import User
from src.schemas.mcp import (
    MCPError,
    MCPLedgerSummary,
)

# Amount validation constants
MIN_AMOUNT = Decimal("0.01")
MAX_AMOUNT = Decimal("999999999.99")


def _find_similar_accounts(
    query: str, accounts: list[Account], threshold: float = 0.4
) -> list[str]:
    """Find accounts with similar names using fuzzy matching."""
    results = []
    query_lower = query.lower()

    for account in accounts:
        name_lower = account.name.lower()
        # Check substring match
        if query_lower in name_lower or name_lower in query_lower:
            results.append((account.name, 1.0))
            continue

        # Check similarity ratio
        ratio = SequenceMatcher(None, query_lower, name_lower).ratio()
        if ratio >= threshold:
            results.append((account.name, ratio))

    # Sort by similarity and return top 5
    return [name for name, _ in sorted(results, key=lambda x: -x[1])[:5]]


def _resolve_account(
    account_ref: str,
    ledger_id: uuid.UUID,
    session: Session,
) -> Account | tuple[str, list[str]]:
    """Resolve account by name or ID.

    Returns:
        Account if found, or tuple of (error_message, suggestions) if not found
    """
    # Try as UUID first
    try:
        account_id = uuid.UUID(account_ref)
        account = session.exec(
            select(Account).where(
                Account.id == account_id,
                Account.ledger_id == ledger_id,
            )
        ).first()
        if account:
            return account
    except ValueError:
        pass  # Not a UUID, try as name

    # Try exact name match
    account = session.exec(
        select(Account).where(
            Account.ledger_id == ledger_id,
            Account.name == account_ref,
        )
    ).first()
    if account:
        return account

    # Get all accounts for suggestions
    all_accounts = list(session.exec(select(Account).where(Account.ledger_id == ledger_id)).all())
    suggestions = _find_similar_accounts(account_ref, all_accounts)

    return (f"找不到科目「{account_ref}」", suggestions)


def _get_user_ledger(
    user: User,
    ledger_id: str | None,
    session: Session,
) -> Ledger | dict[str, Any]:
    """Get the target ledger for the user.

    Returns:
        Ledger if found, or error dict if not found or ambiguous
    """
    # Get all user ledgers
    ledgers = list(session.exec(select(Ledger).where(Ledger.user_id == user.id)).all())

    if not ledgers:
        return {
            "success": False,
            "error": MCPError(
                code="LEDGER_NOT_FOUND",
                message="您還沒有建立任何帳本",
            ).model_dump(),
        }

    # If ledger_id provided, validate it
    if ledger_id:
        try:
            target_id = uuid.UUID(ledger_id)
            for ledger in ledgers:
                if ledger.id == target_id:
                    return ledger
            return {
                "success": False,
                "error": MCPError(
                    code="LEDGER_NOT_FOUND",
                    message="找不到指定的帳本",
                ).model_dump(),
            }
        except ValueError:
            return {
                "success": False,
                "error": MCPError(
                    code="VALIDATION_ERROR",
                    message="無效的帳本 ID 格式",
                ).model_dump(),
            }

    # No ledger_id provided
    if len(ledgers) == 1:
        return ledgers[0]

    # Multiple ledgers, require ledger_id
    return {
        "success": False,
        "error": MCPError(
            code="LEDGER_REQUIRED",
            message="您有多個帳本，請指定 ledger_id",
            available_ledgers=[
                MCPLedgerSummary(
                    id=l.id,
                    name=l.name,
                    description=None,
                    account_count=0,
                    transaction_count=0,
                )
                for l in ledgers
            ],
        ).model_dump(),
    }


def _infer_transaction_type(from_account: Account, to_account: Account) -> TransactionType:
    """Infer transaction type from account types."""
    from_type = from_account.type
    to_type = to_account.type

    if to_type == AccountType.EXPENSE:
        return TransactionType.EXPENSE
    elif from_type == AccountType.INCOME:
        return TransactionType.INCOME
    else:
        return TransactionType.TRANSFER


def _parse_date(date_str: str | None) -> date | dict[str, Any]:
    """Parse date string or return today's date.

    Returns:
        date if valid, or error dict if invalid
    """
    if not date_str:
        return date.today()

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {
            "success": False,
            "error": MCPError(
                code="INVALID_DATE",
                message="日期格式錯誤，請使用 YYYY-MM-DD 格式",
            ).model_dump(),
        }


def create_transaction(
    amount: float,
    from_account: str,
    to_account: str,
    description: str,
    date: str | None,
    notes: str | None,
    ledger_id: str | None,
    session: Session,
    user: User,
) -> dict[str, Any]:
    """Create a new accounting transaction.

    Args:
        amount: Transaction amount (positive number, max 2 decimal places)
        from_account: Source account name or ID
        to_account: Destination account name or ID
        description: Brief description of the transaction
        date: Transaction date in YYYY-MM-DD format (defaults to today)
        notes: Additional notes (optional)
        ledger_id: Target ledger ID (required if user has multiple ledgers)
        session: Database session
        user: Authenticated user

    Returns:
        MCP response dict with success/error status
    """
    # Validate amount
    decimal_amount = Decimal(str(amount))
    if decimal_amount < MIN_AMOUNT:
        return {
            "success": False,
            "error": MCPError(
                code="INVALID_AMOUNT",
                message="金額必須為正數",
            ).model_dump(),
        }

    if decimal_amount > MAX_AMOUNT:
        return {
            "success": False,
            "error": MCPError(
                code="INVALID_AMOUNT",
                message=f"金額不可超過 {MAX_AMOUNT}",
            ).model_dump(),
        }

    # Validate description
    if not description or not description.strip():
        return {
            "success": False,
            "error": MCPError(
                code="VALIDATION_ERROR",
                message="描述不可為空",
            ).model_dump(),
        }

    if len(description) > 255:
        return {
            "success": False,
            "error": MCPError(
                code="VALIDATION_ERROR",
                message="描述最多 255 字元",
            ).model_dump(),
        }

    # Get ledger
    ledger_result = _get_user_ledger(user, ledger_id, session)
    if isinstance(ledger_result, dict):
        return ledger_result
    ledger = ledger_result

    # Resolve accounts
    from_result = _resolve_account(from_account, ledger.id, session)
    if isinstance(from_result, tuple):
        error_msg, suggestions = from_result
        all_accounts = list(
            session.exec(select(Account).where(Account.ledger_id == ledger.id)).all()
        )
        return {
            "success": False,
            "error": MCPError(
                code="ACCOUNT_NOT_FOUND",
                message=error_msg,
                suggestions=suggestions,
                available_accounts=[
                    {
                        "id": str(a.id),
                        "name": a.name,
                        "type": a.type.value,
                        "balance": float(a.balance),
                        "parent_id": str(a.parent_id) if a.parent_id else None,
                        "depth": a.depth,
                    }
                    for a in all_accounts
                ],
            ).model_dump(),
        }
    from_acc = from_result

    to_result = _resolve_account(to_account, ledger.id, session)
    if isinstance(to_result, tuple):
        error_msg, suggestions = to_result
        all_accounts = list(
            session.exec(select(Account).where(Account.ledger_id == ledger.id)).all()
        )
        return {
            "success": False,
            "error": MCPError(
                code="ACCOUNT_NOT_FOUND",
                message=error_msg,
                suggestions=suggestions,
                available_accounts=[
                    {
                        "id": str(a.id),
                        "name": a.name,
                        "type": a.type.value,
                        "balance": float(a.balance),
                        "parent_id": str(a.parent_id) if a.parent_id else None,
                        "depth": a.depth,
                    }
                    for a in all_accounts
                ],
            ).model_dump(),
        }
    to_acc = to_result

    # Validate accounts are different
    if from_acc.id == to_acc.id:
        return {
            "success": False,
            "error": MCPError(
                code="VALIDATION_ERROR",
                message="來源科目和目標科目不可相同",
            ).model_dump(),
        }

    # Parse date
    date_result = _parse_date(date)
    if isinstance(date_result, dict):
        return date_result
    tx_date = date_result

    # Infer transaction type
    tx_type = _infer_transaction_type(from_acc, to_acc)

    # Create transaction
    transaction = Transaction(
        ledger_id=ledger.id,
        date=tx_date,
        description=description.strip(),
        amount=decimal_amount,
        from_account_id=from_acc.id,
        to_account_id=to_acc.id,
        transaction_type=tx_type,
        notes=notes.strip() if notes else None,
    )

    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    # Build response
    return {
        "success": True,
        "data": {
            "transaction": {
                "id": str(transaction.id),
                "date": transaction.date.isoformat(),
                "description": transaction.description,
                "amount": float(transaction.amount),
                "from_account": {
                    "id": str(from_acc.id),
                    "name": from_acc.name,
                },
                "to_account": {
                    "id": str(to_acc.id),
                    "name": to_acc.name,
                },
                "notes": transaction.notes,
            }
        },
        "message": f"交易已建立：從「{from_acc.name}」支出 ${float(decimal_amount):.2f} 至「{to_acc.name}」",
    }


def _parse_date_optional(date_str: str | None) -> date | None | dict[str, Any]:
    """Parse date string or return None.

    Returns:
        date if valid, None if not provided, or error dict if invalid
    """
    if not date_str:
        return None

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {
            "success": False,
            "error": MCPError(
                code="INVALID_DATE",
                message="日期格式錯誤，請使用 YYYY-MM-DD 格式",
            ).model_dump(),
        }


def _resolve_account_optional(
    account_ref: str | None,
    ledger_id: uuid.UUID,
    session: Session,
) -> Account | None | dict[str, Any]:
    """Resolve account by name or ID, returning None if not provided.

    Returns:
        Account if found, None if not provided, or error dict if not found
    """
    if not account_ref:
        return None

    result = _resolve_account(account_ref, ledger_id, session)
    if isinstance(result, tuple):
        error_msg, _ = result
        return {
            "success": False,
            "error": MCPError(
                code="ACCOUNT_NOT_FOUND",
                message=error_msg,
            ).model_dump(),
        }
    return result


# Pagination constants
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def list_transactions(
    ledger_id: str | None,
    account_id: str | None,
    account_name: str | None,
    start_date: str | None,
    end_date: str | None,
    limit: int,
    offset: int,
    session: Session,
    user: User,
) -> dict[str, Any]:
    """Query transaction history with optional filters.

    Args:
        ledger_id: Target ledger ID (required if user has multiple ledgers)
        account_id: Filter by account ID
        account_name: Filter by account name
        start_date: Start date (inclusive) in YYYY-MM-DD format
        end_date: End date (inclusive) in YYYY-MM-DD format
        limit: Maximum number of transactions to return (max 100)
        offset: Number of transactions to skip
        session: Database session
        user: Authenticated user

    Returns:
        MCP response dict with transactions, pagination, and summary
    """
    # Get ledger
    ledger_result = _get_user_ledger(user, ledger_id, session)
    if isinstance(ledger_result, dict):
        return ledger_result
    ledger = ledger_result

    # Parse dates
    parsed_start = _parse_date_optional(start_date)
    if isinstance(parsed_start, dict):
        return parsed_start

    parsed_end = _parse_date_optional(end_date)
    if isinstance(parsed_end, dict):
        return parsed_end

    # Resolve account filter
    filter_account = None
    if account_id:
        filter_account = _resolve_account_optional(account_id, ledger.id, session)
        if isinstance(filter_account, dict):
            return filter_account
    elif account_name:
        filter_account = _resolve_account_optional(account_name, ledger.id, session)
        if isinstance(filter_account, dict):
            return filter_account

    # Normalize pagination parameters
    limit = min(max(1, limit), MAX_LIMIT)
    offset = max(0, offset)

    # Build query for total count and summary
    count_statement = select(Transaction).where(Transaction.ledger_id == ledger.id)

    if parsed_start:
        count_statement = count_statement.where(Transaction.date >= parsed_start)
    if parsed_end:
        count_statement = count_statement.where(Transaction.date <= parsed_end)
    if filter_account:
        count_statement = count_statement.where(
            (Transaction.from_account_id == filter_account.id)
            | (Transaction.to_account_id == filter_account.id)
        )

    # Get all matching transactions for total count and summary
    all_matching = list(session.exec(count_statement).all())
    total_count = len(all_matching)
    total_amount = sum(float(tx.amount) for tx in all_matching)

    # Build query for paginated results
    statement = (
        count_statement.order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    transactions = list(session.exec(statement).all())

    # Build response
    tx_list = []
    for tx in transactions:
        from_acc = session.get(Account, tx.from_account_id)
        to_acc = session.get(Account, tx.to_account_id)

        tx_list.append(
            {
                "id": str(tx.id),
                "date": tx.date.isoformat(),
                "description": tx.description,
                "amount": float(tx.amount),
                "from_account": {
                    "id": str(from_acc.id),
                    "name": from_acc.name,
                },
                "to_account": {
                    "id": str(to_acc.id),
                    "name": to_acc.name,
                },
                "notes": tx.notes,
            }
        )

    has_more = (offset + len(transactions)) < total_count

    # Build message
    if total_count == 0:
        message = "沒有找到符合條件的交易"
    elif has_more:
        start_num = offset + 1
        end_num = offset + len(transactions)
        message = f"找到 {total_count} 筆交易（顯示第 {start_num}-{end_num} 筆）"
    else:
        message = f"找到 {total_count} 筆交易"

    return {
        "success": True,
        "data": {
            "transactions": tx_list,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": has_more,
            },
            "summary": {
                "total_amount": total_amount,
                "transaction_count": total_count,
            },
        },
        "message": message,
    }
