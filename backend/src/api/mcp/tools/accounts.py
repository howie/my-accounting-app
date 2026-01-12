"""MCP tools for account operations.

Based on contracts/mcp-tools.md from 007-api-for-mcp feature.
"""

import uuid
from decimal import Decimal
from typing import Any

from sqlmodel import Session, select

from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction
from src.models.user import User
from src.schemas.mcp import MCPError, MCPLedgerSummary


def _get_user_ledger(
    user: User,
    ledger_id: str | None,
    session: Session,
) -> Ledger | dict[str, Any]:
    """Get the target ledger for the user."""
    ledgers = list(session.exec(select(Ledger).where(Ledger.user_id == user.id)).all())

    if not ledgers:
        return {
            "success": False,
            "error": MCPError(
                code="LEDGER_NOT_FOUND",
                message="您還沒有建立任何帳本",
            ).model_dump(),
        }

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

    if len(ledgers) == 1:
        return ledgers[0]

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


def list_accounts(
    ledger_id: str | None,
    type_filter: str | None,
    include_zero_balance: bool,
    session: Session,
    user: User,
) -> dict[str, Any]:
    """List all accounts with their current balances.

    Args:
        ledger_id: Target ledger ID (required if user has multiple ledgers)
        type_filter: Filter by account type (ASSET, LIABILITY, INCOME, EXPENSE)
        include_zero_balance: Include accounts with zero balance (default True)
        session: Database session
        user: Authenticated user

    Returns:
        MCP response dict with accounts list and summary
    """
    # Get ledger
    ledger_result = _get_user_ledger(user, ledger_id, session)
    if isinstance(ledger_result, dict):
        return ledger_result
    ledger = ledger_result

    # Build query
    statement = select(Account).where(Account.ledger_id == ledger.id)

    # Apply type filter
    if type_filter:
        try:
            account_type = AccountType(type_filter)
            statement = statement.where(Account.type == account_type)
        except ValueError:
            return {
                "success": False,
                "error": MCPError(
                    code="VALIDATION_ERROR",
                    message=f"無效的科目類型: {type_filter}。有效值: ASSET, LIABILITY, INCOME, EXPENSE",
                ).model_dump(),
            }

    # Run query
    accounts = list(session.exec(statement).all())

    # Filter zero balance if requested
    if not include_zero_balance:
        accounts = [a for a in accounts if a.balance != Decimal("0")]

    # Calculate summary
    total_assets = sum(a.balance for a in accounts if a.type == AccountType.ASSET)
    total_liabilities = sum(a.balance for a in accounts if a.type == AccountType.LIABILITY)
    total_income = sum(a.balance for a in accounts if a.type == AccountType.INCOME)
    total_expenses = sum(a.balance for a in accounts if a.type == AccountType.EXPENSE)

    return {
        "success": True,
        "data": {
            "accounts": [
                {
                    "id": str(a.id),
                    "name": a.name,
                    "type": a.type.value,
                    "balance": float(a.balance),
                    "parent_id": str(a.parent_id) if a.parent_id else None,
                    "depth": a.depth,
                }
                for a in accounts
            ],
            "summary": {
                "total_assets": float(total_assets),
                "total_liabilities": float(total_liabilities),
                "total_income": float(total_income),
                "total_expenses": float(total_expenses),
            },
        },
        "message": f"找到 {len(accounts)} 個科目",
    }


def get_account(
    account: str,
    ledger_id: str | None,
    session: Session,
    user: User,
) -> dict[str, Any]:
    """Get detailed information about a specific account.

    Args:
        account: Account name or ID
        ledger_id: Target ledger ID (required if user has multiple ledgers)
        session: Database session
        user: Authenticated user

    Returns:
        MCP response dict with account details and recent transactions
    """
    # Get ledger
    ledger_result = _get_user_ledger(user, ledger_id, session)
    if isinstance(ledger_result, dict):
        return ledger_result
    ledger = ledger_result

    # Find account by ID or name
    found_account = None

    # Try as UUID first
    try:
        account_id = uuid.UUID(account)
        found_account = session.exec(
            select(Account).where(
                Account.id == account_id,
                Account.ledger_id == ledger.id,
            )
        ).first()
    except ValueError:
        pass  # Not a UUID

    # Try by name
    if not found_account:
        found_account = session.exec(
            select(Account).where(
                Account.ledger_id == ledger.id,
                Account.name == account,
            )
        ).first()

    if not found_account:
        return {
            "success": False,
            "error": MCPError(
                code="ACCOUNT_NOT_FOUND",
                message=f"找不到科目「{account}」",
            ).model_dump(),
        }

    # Get children
    children = list(
        session.exec(select(Account).where(Account.parent_id == found_account.id)).all()
    )

    # Get recent transactions (last 10)
    recent_tx = list(
        session.exec(
            select(Transaction)
            .where(
                Transaction.ledger_id == ledger.id,
                (Transaction.from_account_id == found_account.id)
                | (Transaction.to_account_id == found_account.id),
            )
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
            .limit(10)
        ).all()
    )

    # Format recent transactions
    recent_transactions = []
    for tx in recent_tx:
        # Determine amount sign based on account role
        amount = -float(tx.amount) if tx.from_account_id == found_account.id else float(tx.amount)

        recent_transactions.append(
            {
                "id": str(tx.id),
                "date": tx.date.isoformat(),
                "description": tx.description,
                "amount": amount,
            }
        )

    return {
        "success": True,
        "data": {
            "account": {
                "id": str(found_account.id),
                "name": found_account.name,
                "type": found_account.type.value,
                "balance": float(found_account.balance),
                "parent_id": str(found_account.parent_id) if found_account.parent_id else None,
                "depth": found_account.depth,
                "is_system": found_account.is_system,
                "children": [
                    {
                        "id": str(c.id),
                        "name": c.name,
                        "type": c.type.value,
                        "balance": float(c.balance),
                        "parent_id": str(c.parent_id) if c.parent_id else None,
                        "depth": c.depth,
                    }
                    for c in children
                ],
                "recent_transactions": recent_transactions,
            }
        },
        "message": f"「{found_account.name}」餘額為 ${float(found_account.balance):,.2f}",
    }
