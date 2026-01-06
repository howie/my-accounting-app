from typing import Optional
from src.myab.models.user_account import UserAccount
from src.myab.persistence.repositories.user_account_repository import UserAccountRepository
# For password hashing, we'd typically use a library like 'bcrypt' or 'passlib'
# For this example, we'll use a simple placeholder for password hashing
import hashlib

class UserAccountService:
    def __init__(self, user_account_repository: UserAccountRepository):
        self.user_account_repository = user_account_repository

    def _hash_password(self, password: str) -> str:
        # In a real application, use a strong, salted hashing algorithm like bcrypt
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user_account(self, username: str, password: str) -> tuple[Optional[UserAccount], str]:
        if self.user_account_repository.get_by_username(username):
            return None, "Username already exists."
        
        hashed_password = self._hash_password(password)
        new_user = UserAccount(username=username, password_hash=hashed_password)
        created_user = self.user_account_repository.add(new_user)
        return created_user, "User account created successfully."

    def authenticate_user(self, username: str, password: str) -> Optional[UserAccount]:
        user = self.user_account_repository.get_by_username(username)
        if user and user.password_hash == self._hash_password(password):
            return user
        return None

    def get_user_account_by_id(self, user_id: int) -> Optional[UserAccount]:
        return self.user_account_repository.get_by_id(user_id)

    def get_user_account_by_username(self, username: str) -> Optional[UserAccount]:
        return self.user_account_repository.get_by_username(username)

    def update_user_account(self, user_account: UserAccount) -> bool:
        return self.user_account_repository.update(user_account)

    def delete_user_account(self, user_id: int) -> bool:
        # TODO: Add logic to prevent deletion if user has associated ledgers
        return self.user_account_repository.delete(user_id)