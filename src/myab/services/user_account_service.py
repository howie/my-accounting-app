from myab.models.user_account import UserAccount
from myab.persistence.repositories.user_account_repository import UserAccountRepository

class UserAccountService:
    def __init__(self, repo: UserAccountRepository):
        self.repo = repo

    def create_user(self, username: str, password: str) -> int:
        # In a real app, hash the password here!
        user = UserAccount(username=username, password_hash=password)
        return self.repo.create(user)

    def authenticate_user(self, username: str, password: str) -> UserAccount | None:
        user = self.repo.get_by_username(username)
        # In a real app, verify hash here!
        if user and user.password_hash == password:
            return user
        return None
