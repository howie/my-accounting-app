"""User model."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.api_token import ApiToken
    from src.models.gmail_connection import GmailConnection
    from src.models.user_bank_setting import UserBankSetting


class UserBase(SQLModel):
    """User base schema."""

    email: str = Field(max_length=255, unique=True, index=True)
    display_name: str | None = Field(default=None, max_length=100)


class User(UserBase, table=True):
    """User database model."""

    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    api_tokens: list["ApiToken"] = Relationship(back_populates="user")
    gmail_connection: "GmailConnection | None" = Relationship(back_populates="user")
    bank_settings: list["UserBankSetting"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    """Schema for creating a user."""

    pass


class UserRead(UserBase):
    """Schema for reading a user."""

    id: uuid.UUID
    created_at: datetime


class UserSetup(SQLModel):
    """Schema for initial user setup."""

    email: str = Field(max_length=255)
