"""User model."""

import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    """User base schema."""

    email: str = Field(max_length=255, unique=True, index=True)


class User(UserBase, table=True):
    """User database model."""

    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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
