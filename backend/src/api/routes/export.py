from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import aliased, selectinload
from sqlmodel import select

from src.api.deps import SessionDep, get_current_user
from src.models.account import Account
from src.models.ledger import Ledger
from src.models.transaction import Transaction
from src.models.user import User
from src.services.export_service import ExportFormat, ExportService

router = APIRouter()


@router.get("/transactions")
def export_transactions(
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    format: ExportFormat,
    start_date: date | None = None,
    end_date: date | None = None,
    account_id: UUID | None = None,
):
    """
    Export transactions in CSV or HTML format.
    """
    # 1. Validation
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="Start date cannot be after end date")

    # 2. Verify account ownership if provided
    if account_id:
        account = session.get(Account, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Verify ledger ownership
        ledger = session.get(Ledger, account.ledger_id)
        if not ledger or ledger.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Account not found or access denied")

    # 3. Fetch Data
    # Create aliases for joining
    FromAccount = aliased(Account, name="from_account")
    ToAccount = aliased(Account, name="to_account")

    # Secure query: only transactions belonging to user's ledgers
    query = select(Transaction).join(Ledger).where(Ledger.user_id == current_user.id)

    # Joins for mapping
    query = query.outerjoin(FromAccount, Transaction.from_account_id == FromAccount.id).outerjoin(
        ToAccount, Transaction.to_account_id == ToAccount.id
    )

    # Eager load for service
    query = query.options(
        selectinload(Transaction.from_account), selectinload(Transaction.to_account)
    )

    # Filter by Date
    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)

    # Filter by Account
    if account_id:
        # Transactions WHERE from_account_id = X OR to_account_id = X
        query = query.where(
            (Transaction.from_account_id == account_id) | (Transaction.to_account_id == account_id)
        )

    # Execute
    # Order by date desc
    query = query.order_by(Transaction.date.desc())

    transactions = session.exec(query).all()

    # 4. Generate Output
    export_service = ExportService(session)
    filename_date = date.today().strftime("%Y%m%d")

    if format == ExportFormat.CSV:
        filename = f"export_{filename_date}.csv"
        # StreamingResponse takes a generator
        return StreamingResponse(
            export_service.generate_csv_content(transactions),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    elif format == ExportFormat.HTML:
        filename = f"export_{filename_date}.html"

        # Determine metadata string
        date_range_str = "All Time"
        if start_date and end_date:
            date_range_str = f"{start_date} to {end_date}"
        elif start_date:
            date_range_str = f"From {start_date}"
        elif end_date:
            date_range_str = f"Until {end_date}"

        acc_name = None
        if account_id:
            # We already fetched 'account' above if account_id is present
            acc_name = account.name  # type: ignore (checked above)

        html_content = export_service.generate_html_content(transactions, date_range_str, acc_name)

        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
