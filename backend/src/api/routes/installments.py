from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.api.deps import get_session
from src.schemas.advanced import InstallmentPlanCreate, InstallmentPlanRead
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
