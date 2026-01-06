"""Custom exception classes for the application."""

from typing import Any


class LedgerOneException(Exception):
    """Base exception for LedgerOne application."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(LedgerOneException):
    """Resource not found."""

    pass


class ValidationError(LedgerOneException):
    """Validation error."""

    pass


class ConflictError(LedgerOneException):
    """Resource conflict (e.g., duplicate)."""

    pass


class UnbalancedTransactionError(ValidationError):
    """Transaction debits do not equal credits."""

    def __init__(
        self,
        message: str = "Transaction debits must equal credits",
        from_account: str | None = None,
        to_account: str | None = None,
    ):
        details = {}
        if from_account:
            details["from_account"] = from_account
        if to_account:
            details["to_account"] = to_account
        super().__init__(message, details)


class InvalidTransactionTypeError(ValidationError):
    """Transaction type does not match account types."""

    def __init__(
        self,
        message: str,
        from_account_type: str | None = None,
        to_account_type: str | None = None,
        transaction_type: str | None = None,
    ):
        details = {}
        if from_account_type:
            details["from_account_type"] = from_account_type
        if to_account_type:
            details["to_account_type"] = to_account_type
        if transaction_type:
            details["transaction_type"] = transaction_type
        super().__init__(message, details)


class SystemAccountError(ValidationError):
    """Operation not allowed on system accounts."""

    def __init__(self, account_name: str, operation: str = "delete"):
        message = f"Cannot {operation} system account: {account_name}"
        super().__init__(message, {"account_name": account_name, "operation": operation})


class AccountHasTransactionsError(ConflictError):
    """Cannot delete account with existing transactions."""

    def __init__(self, account_name: str):
        message = f"Cannot delete account '{account_name}' with existing transactions"
        super().__init__(message, {"account_name": account_name})
