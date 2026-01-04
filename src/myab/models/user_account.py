from typing import Optional
from src.myab.models.base import BaseModel

class UserAccount(BaseModel):
    """
    Represents a unique user with password protection.
    Each user account contains multiple ledgers.
    """
    def __init__(self, username: str, password_hash: str, id: Optional[int] = None,
                 creation_timestamp: Optional[str] = None,
                 modification_timestamp: Optional[str] = None):
        super().__init__(id, creation_timestamp, modification_timestamp)
        self.username = username
        self.password_hash = password_hash

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "username": self.username,
            "password_hash": self.password_hash
        })
        return data

    def __repr__(self) -> str:
        return f"UserAccount(id={self.id}, username='{self.username}')"