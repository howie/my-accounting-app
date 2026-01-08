# API Contract: Dashboard Service

**Date**: 2026-01-06
**Feature**: 002-ui-layout-dashboard
**Base URL**: `/api/v1`

---

## Overview

Dashboard service provides aggregated financial data for the dashboard homepage and sidebar navigation. All endpoints are read-only and require an active ledger context.

---

## Endpoints

### 1. Get Dashboard Summary

Retrieve aggregated financial metrics for the dashboard.

**Endpoint**: `GET /ledgers/{ledger_id}/dashboard`

**Path Parameters**:

| Parameter | Type | Required | Description                          |
| --------- | ---- | -------- | ------------------------------------ |
| ledger_id | UUID | Yes      | The ledger to get dashboard data for |

**Response**: `200 OK`

```json
{
  "total_assets": 21847.0,
  "current_month": {
    "income": 2992.0,
    "expenses": 1419.0,
    "net_cash_flow": 1573.0
  },
  "trends": [
    {
      "month": "Aug",
      "year": 2025,
      "income": 2500.0,
      "expenses": 1200.0
    },
    {
      "month": "Sep",
      "year": 2025,
      "income": 2800.0,
      "expenses": 1400.0
    },
    {
      "month": "Oct",
      "year": 2025,
      "income": 3100.0,
      "expenses": 1100.0
    },
    {
      "month": "Nov",
      "year": 2025,
      "income": 2900.0,
      "expenses": 1300.0
    },
    {
      "month": "Dec",
      "year": 2025,
      "income": 3200.0,
      "expenses": 1500.0
    },
    {
      "month": "Jan",
      "year": 2026,
      "income": 2992.0,
      "expenses": 1419.0
    }
  ]
}
```

**Error Responses**:

| Status | Code             | Description                         |
| ------ | ---------------- | ----------------------------------- |
| 404    | LEDGER_NOT_FOUND | Ledger with given ID does not exist |

**Notes**:

- `total_assets` is the sum of all ASSET account balances
- `trends` contains up to 6 months of data, ordered chronologically
- If less than 6 months of data exists, only available months are returned
- Empty ledger returns zeros for all values

---

### 2. Get Accounts by Category

Retrieve all accounts grouped by their category type for sidebar display.

**Endpoint**: `GET /ledgers/{ledger_id}/accounts/by-category`

**Path Parameters**:

| Parameter | Type | Required | Description                    |
| --------- | ---- | -------- | ------------------------------ |
| ledger_id | UUID | Yes      | The ledger to get accounts for |

**Response**: `200 OK`

```json
{
  "categories": [
    {
      "type": "ASSET",
      "accounts": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "name": "Cash",
          "balance": 15000.0
        },
        {
          "id": "550e8400-e29b-41d4-a716-446655440002",
          "name": "Bank Account",
          "balance": 6847.0
        }
      ]
    },
    {
      "type": "LIABILITY",
      "accounts": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440003",
          "name": "Credit Card",
          "balance": 500.0
        }
      ]
    },
    {
      "type": "INCOME",
      "accounts": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440004",
          "name": "Salary",
          "balance": 2992.0
        }
      ]
    },
    {
      "type": "EXPENSE",
      "accounts": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440005",
          "name": "Food",
          "balance": 800.0
        },
        {
          "id": "550e8400-e29b-41d4-a716-446655440006",
          "name": "Transport",
          "balance": 200.0
        }
      ]
    }
  ]
}
```

**Error Responses**:

| Status | Code             | Description                         |
| ------ | ---------------- | ----------------------------------- |
| 404    | LEDGER_NOT_FOUND | Ledger with given ID does not exist |

**Notes**:

- Categories are returned in fixed order: ASSET, LIABILITY, INCOME, EXPENSE
- Empty categories are still included with empty `accounts` array
- Accounts within each category are ordered alphabetically by name

---

### 3. Get Account Transactions

Retrieve paginated transactions for a specific account.

**Endpoint**: `GET /accounts/{account_id}/transactions`

**Path Parameters**:

| Parameter  | Type | Required | Description                         |
| ---------- | ---- | -------- | ----------------------------------- |
| account_id | UUID | Yes      | The account to get transactions for |

**Query Parameters**:

| Parameter | Type | Required | Default | Description              |
| --------- | ---- | -------- | ------- | ------------------------ |
| page      | int  | No       | 1       | Page number (1-indexed)  |
| page_size | int  | No       | 50      | Items per page (max 100) |

**Response**: `200 OK`

```json
{
  "account_id": "550e8400-e29b-41d4-a716-446655440001",
  "account_name": "Cash",
  "transactions": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "date": "2026-01-05",
      "description": "Grocery shopping",
      "amount": 150.0,
      "type": "EXPENSE",
      "other_account_name": "Food"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440002",
      "date": "2026-01-03",
      "description": "Monthly salary",
      "amount": 5000.0,
      "type": "INCOME",
      "other_account_name": "Salary"
    }
  ],
  "total_count": 125,
  "page": 1,
  "page_size": 50,
  "has_more": true
}
```

**Error Responses**:

| Status | Code              | Description                          |
| ------ | ----------------- | ------------------------------------ |
| 404    | ACCOUNT_NOT_FOUND | Account with given ID does not exist |
| 400    | INVALID_PAGE      | Page number is invalid               |
| 400    | INVALID_PAGE_SIZE | Page size exceeds maximum (100)      |

**Notes**:

- Transactions are ordered by date DESC (newest first)
- `other_account_name` shows the counterpart account in the transaction
- For expenses: other account is the expense category
- For income: other account is the income source
- For transfers: other account is the destination/source asset

---

## Type Definitions

### AccountType Enum

```python
class AccountType(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
```

### TransactionType Enum

```python
class TransactionType(str, Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    TRANSFER = "TRANSFER"
```

---

## Service Interface

```python
class DashboardService:
    """Service for dashboard data aggregation."""

    def get_dashboard_summary(
        self,
        ledger_id: UUID,
        session: Session
    ) -> DashboardResponse:
        """
        Get aggregated dashboard data.

        Args:
            ledger_id: The ledger UUID
            session: Database session

        Returns:
            DashboardResponse with total_assets, current_month, and trends

        Raises:
            LedgerNotFoundError: If ledger doesn't exist
        """
        ...

    def get_accounts_by_category(
        self,
        ledger_id: UUID,
        session: Session
    ) -> AccountsByCategoryResponse:
        """
        Get all accounts grouped by category type.

        Args:
            ledger_id: The ledger UUID
            session: Database session

        Returns:
            AccountsByCategoryResponse with categorized accounts

        Raises:
            LedgerNotFoundError: If ledger doesn't exist
        """
        ...

    def get_account_transactions(
        self,
        account_id: UUID,
        page: int,
        page_size: int,
        session: Session
    ) -> AccountTransactionsResponse:
        """
        Get paginated transactions for an account.

        Args:
            account_id: The account UUID
            page: Page number (1-indexed)
            page_size: Items per page
            session: Database session

        Returns:
            AccountTransactionsResponse with paginated transactions

        Raises:
            AccountNotFoundError: If account doesn't exist
            InvalidPageError: If page number is invalid
        """
        ...
```

---

## Caching Strategy

| Endpoint             | Cache Duration | Invalidation            |
| -------------------- | -------------- | ----------------------- |
| Dashboard summary    | 5 minutes      | On any transaction CRUD |
| Accounts by category | 10 minutes     | On account CRUD         |
| Account transactions | No cache       | N/A (paginated)         |

Cache keys:

- `dashboard:{ledger_id}`
- `accounts_by_category:{ledger_id}`
