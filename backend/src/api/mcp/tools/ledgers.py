"""MCP tools for ledger operations.

Based on contracts/mcp-tools.md from 007-api-for-mcp feature.
"""

from typing import Any

from sqlmodel import Session, func, select

from src.models.account import Account
from src.models.ledger import Ledger
from src.models.transaction import Transaction
from src.models.user import User


def list_ledgers(
    session: Session,
    user: User,
) -> dict[str, Any]:
    """List all ledgers available to the authenticated user.

    Args:
        session: Database session
        user: Authenticated user

    Returns:
        MCP response dict with ledgers list and default_ledger_id
    """
    # Get all user ledgers
    ledgers = list(
        session.exec(
            select(Ledger).where(Ledger.user_id == user.id).order_by(Ledger.created_at)
        ).all()
    )

    # Build ledger list with counts
    ledger_list = []
    for ledger in ledgers:
        # Count accounts
        account_count = session.exec(
            select(func.count(Account.id)).where(Account.ledger_id == ledger.id)
        ).one()

        # Count transactions
        transaction_count = session.exec(
            select(func.count(Transaction.id)).where(Transaction.ledger_id == ledger.id)
        ).one()

        ledger_list.append(
            {
                "id": str(ledger.id),
                "name": ledger.name,
                "description": None,  # Ledger model doesn't have description field
                "account_count": account_count,
                "transaction_count": transaction_count,
            }
        )

    # Determine default ledger
    default_ledger_id = str(ledgers[0].id) if ledgers else None

    # Build message
    count = len(ledgers)
    if count == 0:
        message = "您還沒有建立任何帳本"
    elif count == 1:
        message = "您有 1 個帳本"
    else:
        message = f"您有 {count} 個帳本"

    return {
        "success": True,
        "data": {
            "ledgers": ledger_list,
            "default_ledger_id": default_ledger_id,
        },
        "message": message,
    }
