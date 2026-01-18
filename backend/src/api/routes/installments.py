from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.api.deps import get_session
from src.schemas.advanced import InstallmentPlanCreate, InstallmentPlanRead
from src.schemas.transaction import TransactionRead
from src.services.installment_service import InstallmentService

router = APIRouter()


@router.post("", response_model=InstallmentPlanRead, status_code=201)
def create_installment_plan(data: InstallmentPlanCreate, session: Session = Depends(get_session)):
    service = InstallmentService(session)
    try:
        return service.create_installment_plan(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[InstallmentPlanRead])
def list_installment_plans(session: Session = Depends(get_session)):
    service = InstallmentService(session)
    return service.list_installment_plans()


@router.get("/{plan_id}", response_model=InstallmentPlanRead)
def get_installment_plan(plan_id: UUID, session: Session = Depends(get_session)):
    service = InstallmentService(session)
    try:
        return service.get_installment_plan(str(plan_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{plan_id}/transactions", response_model=list[TransactionRead])
def get_plan_transactions(plan_id: UUID, session: Session = Depends(get_session)):
    service = InstallmentService(session)
    # Validate plan exists first
    try:
        service.get_installment_plan(str(plan_id))
        return service.get_plan_transactions(str(plan_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
