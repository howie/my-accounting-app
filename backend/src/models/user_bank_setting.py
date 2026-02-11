"""UserBankSetting model for per-user bank configuration.

Based on data-model.md for 011-gmail-cc-statement-import feature.
Stores which banks are enabled and their PDF decryption passwords (encrypted).
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.account import Account
    from src.models.user import User


class UserBankSetting(SQLModel, table=True):
    """Stores per-user configuration for each bank.

    Each user can have one setting per bank.
    PDF passwords are encrypted using Fernet symmetric encryption.
    """

    __tablename__ = "user_bank_settings"
    __table_args__ = (UniqueConstraint("user_id", "bank_code", name="uq_user_bank"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    # Bank identification
    bank_code: str = Field(max_length=20)  # e.g., "CTBC", "CATHAY"

    # Configuration
    is_enabled: bool = Field(default=False)

    # Encrypted PDF password (Fernet encrypted, null if not set)
    encrypted_pdf_password: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Linked credit card account in the ledger
    credit_card_account_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="accounts.id",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    user: "User" = Relationship(back_populates="bank_settings")
    credit_card_account: "Account | None" = Relationship()
