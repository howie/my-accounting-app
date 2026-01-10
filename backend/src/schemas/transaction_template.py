"""TransactionTemplate-related schemas for request/response validation.

Based on contracts/templates.yaml from 004-transaction-entry feature.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator
from sqlmodel import SQLModel

from src.models.transaction import TransactionType


class TransactionTemplateCreate(SQLModel):
    """Schema for creating a new transaction template."""

    name: str = Field(min_length=1, max_length=50)
    transaction_type: TransactionType
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: Decimal = Field(
        ge=Decimal("0.01"), le=Decimal("999999999.99"), max_digits=15, decimal_places=2
    )
    description: str = Field(min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Ensure name is not whitespace only."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        """Ensure description is not whitespace only."""
        if not v.strip():
            raise ValueError("Description cannot be empty or whitespace only")
        return v.strip()


class TransactionTemplateUpdate(SQLModel):
    """Schema for updating a transaction template (partial update)."""

    name: str | None = Field(default=None, min_length=1, max_length=50)
    transaction_type: TransactionType | None = None
    from_account_id: uuid.UUID | None = None
    to_account_id: uuid.UUID | None = None
    amount: Decimal | None = Field(
        default=None,
        ge=Decimal("0.01"),
        le=Decimal("999999999.99"),
        max_digits=15,
        decimal_places=2,
    )
    description: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        """Ensure name is not whitespace only."""
        if v is None:
            return v
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str | None) -> str | None:
        """Ensure description is not whitespace only."""
        if v is None:
            return v
        if not v.strip():
            raise ValueError("Description cannot be empty or whitespace only")
        return v.strip()


class TransactionTemplateRead(SQLModel):
    """Schema for reading a transaction template (full details)."""

    id: uuid.UUID
    ledger_id: uuid.UUID
    name: str
    transaction_type: TransactionType
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: Decimal
    description: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class TransactionTemplateListItem(SQLModel):
    """Schema for template list items."""

    id: uuid.UUID
    name: str
    transaction_type: TransactionType
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: Decimal
    description: str
    sort_order: int


class TransactionTemplateList(SQLModel):
    """List of transaction templates."""

    data: list[TransactionTemplateListItem]
    total: int


class ReorderTemplatesRequest(SQLModel):
    """Schema for reordering templates."""

    template_ids: list[uuid.UUID] = Field(
        description="Ordered list of template IDs representing the new order"
    )

    @field_validator("template_ids")
    @classmethod
    def validate_not_empty(cls, v: list[uuid.UUID]) -> list[uuid.UUID]:
        """Ensure at least one template ID is provided."""
        if not v:
            raise ValueError("At least one template ID must be provided")
        return v


class ApplyTemplateRequest(SQLModel):
    """Schema for applying a template to create a transaction."""

    date: str | None = Field(
        default=None,
        description="Transaction date (YYYY-MM-DD). Defaults to today if not provided.",
    )
    notes: str | None = Field(
        default=None,
        max_length=500,
        description="Optional notes for the transaction",
    )

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: str | None) -> str | None:
        """Validate notes length."""
        if v is not None and len(v) > 500:
            raise ValueError("Notes must be at most 500 characters")
        return v
