from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session

from src.api.deps import get_session
from src.schemas.advanced import (
    RecurringTransactionCreate,
    RecurringTransactionDue,
    RecurringTransactionRead,
)
from src.schemas.transaction import TransactionRead
from src.services.recurring_service import RecurringService

router = APIRouter()


class ApproveRequest(BaseModel):
    date: date


@router.post("", response_model=RecurringTransactionRead, status_code=201)
def create_recurring_transaction(
    data: RecurringTransactionCreate, session: Session = Depends(get_session)
):
    service = RecurringService(session)
    try:
        return service.create_recurring_transaction(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/due", response_model=list[RecurringTransactionDue])
def check_due_transactions(
    check_date: date | None = Query(default=None), session: Session = Depends(get_session)
):
    service = RecurringService(session)
    # Default to today if not provided
    target_date = check_date or date.today()
    return service.get_due_transactions(target_date)


@router.post("/{recurring_id}/approve", response_model=TransactionRead, status_code=201)
def approve_transaction(
    recurring_id: UUID, approval_data: ApproveRequest, session: Session = Depends(get_session)
):
    service = RecurringService(session)
    try:
        return service.approve_transaction(recurring_id, approval_data.date)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
