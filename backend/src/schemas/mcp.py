"""MCP response schemas for LedgerOne API.

These schemas define the response format for all MCP tools,
ensuring consistent structure for AI assistants.
"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MCPAccountRef(BaseModel):
    """Account reference in MCP responses."""

    id: UUID
    name: str


class MCPAccountSummary(BaseModel):
    """Account summary for list_accounts and get_account tools."""

    id: UUID
    name: str
    type: str  # ASSET, LIABILITY, INCOME, EXPENSE
    balance: Decimal
    parent_id: UUID | None = None
    depth: int


class MCPAccountDetail(MCPAccountSummary):
    """Detailed account information with recent transactions."""

    is_system: bool = False
    children: list["MCPAccountSummary"] = Field(default_factory=list)
    recent_transactions: list["MCPTransactionSummary"] = Field(default_factory=list)


class MCPTransactionSummary(BaseModel):
    """Transaction summary for MCP responses."""

    id: UUID
    date: str  # YYYY-MM-DD
    description: str
    amount: Decimal
    from_account: MCPAccountRef
    to_account: MCPAccountRef
    notes: str | None = None


class MCPLedgerSummary(BaseModel):
    """Ledger summary for list_ledgers tool."""

    id: UUID
    name: str
    description: str | None = None
    account_count: int
    transaction_count: int


class MCPPagination(BaseModel):
    """Pagination information for list responses."""

    total: int
    limit: int
    offset: int
    has_more: bool


class MCPAccountListSummary(BaseModel):
    """Summary statistics for account list."""

    total_assets: Decimal
    total_liabilities: Decimal
    total_income: Decimal
    total_expenses: Decimal


class MCPTransactionListSummary(BaseModel):
    """Summary statistics for transaction list."""

    total_amount: Decimal
    transaction_count: int


class MCPError(BaseModel):
    """Error details for MCP responses."""

    code: str
    message: str
    suggestions: list[str] = Field(default_factory=list)
    available_accounts: list[MCPAccountSummary] | None = None
    available_ledgers: list[MCPLedgerSummary] | None = None


class MCPResponse(BaseModel):
    """Standard MCP response wrapper."""

    success: bool
    data: dict[str, Any] | None = None
    message: str | None = None
    error: MCPError | None = None

    @classmethod
    def ok(cls, data: dict[str, Any], message: str) -> "MCPResponse":
        """Create a successful response."""
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, error: MCPError) -> "MCPResponse":
        """Create a failed response."""
        return cls(success=False, error=error)


# Update forward references
MCPAccountDetail.model_rebuild()
