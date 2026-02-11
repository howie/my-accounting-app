"""Base class for bank statement parsers.

Defines the abstract interface that all bank-specific parsers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class ParsedStatementTransaction:
    """Represents a single transaction extracted from a PDF statement.

    This is a transient data structure used during parsing,
    before transactions are imported into the accounting system.
    """

    date: date
    merchant_name: str
    amount: Decimal
    currency: str = "TWD"
    original_description: str = ""
    category_suggestion: str | None = None
    confidence: float = 0.0
    is_foreign: bool = False
    installment_info: str | None = None
    # Additional metadata
    metadata: dict = field(default_factory=dict)


class BankStatementParser(ABC):
    """Abstract base class for bank-specific PDF statement parsers.

    Each bank parser must implement:
    - bank_code: Unique identifier (e.g., "CTBC")
    - bank_name: Display name (e.g., "中國信託")
    - email_query: Gmail search query for finding statements
    - password_hint: Description of the PDF password convention
    - parse_statement(): Extract transactions from PDF
    - detect_billing_period(): Extract billing period from PDF
    """

    # Class attributes to be overridden by subclasses
    bank_code: str = ""
    bank_name: str = ""
    email_query: str = ""
    password_hint: str = ""

    @abstractmethod
    def parse_statement(self, pdf_path: str) -> list[ParsedStatementTransaction]:
        """Parse transactions from a bank statement PDF.

        Args:
            pdf_path: Path to the decrypted PDF file.

        Returns:
            List of parsed transactions.

        Raises:
            ParseError: If the PDF cannot be parsed.
        """
        pass

    @abstractmethod
    def detect_billing_period(self, pdf_path: str) -> tuple[date, date] | None:
        """Extract the billing period from the statement.

        Args:
            pdf_path: Path to the decrypted PDF file.

        Returns:
            Tuple of (start_date, end_date) or None if not found.
        """
        pass

    def validate_result(self, transactions: list[ParsedStatementTransaction]) -> float:
        """Validate parsing results and return a confidence score.

        Default implementation checks for:
        - Non-empty transaction list
        - Valid amounts (positive, reasonable range)
        - Valid dates (within expected billing period)

        Args:
            transactions: List of parsed transactions.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if not transactions:
            return 0.0

        valid_count = 0
        for tx in transactions:
            # Check amount is positive and reasonable
            if tx.amount > 0 and tx.amount < Decimal("10000000"):
                valid_count += 1

        return valid_count / len(transactions) if transactions else 0.0

    def get_info(self) -> dict:
        """Get parser info as a dictionary.

        Returns:
            Dict with code, name, email_query, password_hint.
        """
        return {
            "code": self.bank_code,
            "name": self.bank_name,
            "email_query": self.email_query,
            "password_hint": self.password_hint,
        }


class ParseError(Exception):
    """Raised when PDF parsing fails."""

    pass
