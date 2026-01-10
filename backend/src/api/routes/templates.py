"""Transaction Template API routes.

Based on contracts/templates.yaml from 004-transaction-entry feature.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from src.api.deps import get_current_user_id, get_session
from src.core.exceptions import NotFoundError, ValidationError
from src.schemas.transaction import TransactionRead
from src.schemas.transaction_template import (
    ApplyTemplateRequest,
    ReorderTemplatesRequest,
    TransactionTemplateCreate,
    TransactionTemplateList,
    TransactionTemplateListItem,
    TransactionTemplateRead,
    TransactionTemplateUpdate,
)
from src.services.ledger_service import LedgerService
from src.services.template_service import TemplateService

router = APIRouter(prefix="/ledgers/{ledger_id}/templates", tags=["templates"])


def get_template_service(
    session: Annotated[Session, Depends(get_session)],
) -> TemplateService:
    """Dependency to get TemplateService instance."""
    return TemplateService(session)


def get_ledger_service(session: Annotated[Session, Depends(get_session)]) -> LedgerService:
    """Dependency to get LedgerService instance."""
    return LedgerService(session)


def verify_ledger_exists(
    ledger_id: uuid.UUID,
    ledger_service: Annotated[LedgerService, Depends(get_ledger_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> uuid.UUID:
    """Verify ledger exists and belongs to user."""
    ledger = ledger_service.get_ledger(ledger_id, user_id)
    if not ledger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ledger not found",
        )
    return ledger_id


@router.get("", response_model=TransactionTemplateList)
def list_templates(
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TemplateService, Depends(get_template_service)],
) -> TransactionTemplateList:
    """List all templates for a ledger."""
    templates = service.list_templates(ledger_id)
    return TransactionTemplateList(
        data=[
            TransactionTemplateListItem(
                id=t.id,
                name=t.name,
                transaction_type=t.transaction_type,
                from_account_id=t.from_account_id,
                to_account_id=t.to_account_id,
                amount=t.amount,
                description=t.description,
                sort_order=t.sort_order,
            )
            for t in templates
        ],
        total=len(templates),
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TransactionTemplateRead)
def create_template(
    data: TransactionTemplateCreate,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TemplateService, Depends(get_template_service)],
) -> TransactionTemplateRead:
    """Create a new transaction template."""
    try:
        template = service.create_template(ledger_id, data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e.message),
        )

    return TransactionTemplateRead(
        id=template.id,
        ledger_id=template.ledger_id,
        name=template.name,
        transaction_type=template.transaction_type,
        from_account_id=template.from_account_id,
        to_account_id=template.to_account_id,
        amount=template.amount,
        description=template.description,
        sort_order=template.sort_order,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.patch("/reorder", response_model=TransactionTemplateList)
def reorder_templates(
    data: ReorderTemplatesRequest,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TemplateService, Depends(get_template_service)],
) -> TransactionTemplateList:
    """Reorder templates."""
    try:
        templates = service.reorder_templates(ledger_id, data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e.message),
        )

    return TransactionTemplateList(
        data=[
            TransactionTemplateListItem(
                id=t.id,
                name=t.name,
                transaction_type=t.transaction_type,
                from_account_id=t.from_account_id,
                to_account_id=t.to_account_id,
                amount=t.amount,
                description=t.description,
                sort_order=t.sort_order,
            )
            for t in templates
        ],
        total=len(templates),
    )


@router.get("/{template_id}", response_model=TransactionTemplateRead)
def get_template(
    template_id: uuid.UUID,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TemplateService, Depends(get_template_service)],
) -> TransactionTemplateRead:
    """Get a single template."""
    try:
        template = service.get_template(template_id, ledger_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    return TransactionTemplateRead(
        id=template.id,
        ledger_id=template.ledger_id,
        name=template.name,
        transaction_type=template.transaction_type,
        from_account_id=template.from_account_id,
        to_account_id=template.to_account_id,
        amount=template.amount,
        description=template.description,
        sort_order=template.sort_order,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.patch("/{template_id}", response_model=TransactionTemplateRead)
def update_template(
    template_id: uuid.UUID,
    data: TransactionTemplateUpdate,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TemplateService, Depends(get_template_service)],
) -> TransactionTemplateRead:
    """Update a template (partial update)."""
    try:
        template = service.update_template(template_id, ledger_id, data)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e.message),
        )

    return TransactionTemplateRead(
        id=template.id,
        ledger_id=template.ledger_id,
        name=template.name,
        transaction_type=template.transaction_type,
        from_account_id=template.from_account_id,
        to_account_id=template.to_account_id,
        amount=template.amount,
        description=template.description,
        sort_order=template.sort_order,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: uuid.UUID,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TemplateService, Depends(get_template_service)],
) -> None:
    """Delete a template."""
    try:
        service.delete_template(template_id, ledger_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )


@router.post(
    "/{template_id}/apply", status_code=status.HTTP_201_CREATED, response_model=TransactionRead
)
def apply_template(
    template_id: uuid.UUID,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TemplateService, Depends(get_template_service)],
    data: ApplyTemplateRequest | None = None,
) -> TransactionRead:
    """Apply a template to create a new transaction."""
    try:
        transaction = service.apply_template(template_id, ledger_id, data)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e.message),
        )

    return TransactionRead(
        id=transaction.id,
        ledger_id=transaction.ledger_id,
        date=transaction.date,
        description=transaction.description,
        amount=transaction.amount,
        from_account_id=transaction.from_account_id,
        to_account_id=transaction.to_account_id,
        transaction_type=transaction.transaction_type,
        notes=transaction.notes,
        amount_expression=transaction.amount_expression,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at,
    )
