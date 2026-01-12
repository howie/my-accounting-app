# MCP Tool Contracts

**Feature**: 007-api-for-mcp
**Date**: 2026-01-11
**Protocol**: Model Context Protocol (MCP)

## Overview

This document defines the contract for all MCP tools exposed by the LedgerOne accounting system. Each tool follows the MCP specification and can be invoked by AI assistants (Claude, ChatGPT, etc.).

## Authentication

All tools require a valid API token in the request context. The token is validated against the `api_tokens` table.

```
Authorization: Bearer <token>
```

## Tool Definitions

### 1. create_transaction

Creates a new accounting transaction with double-entry bookkeeping.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "amount": {
      "type": "number",
      "description": "Transaction amount (positive number, max 2 decimal places)",
      "minimum": 0.01,
      "maximum": 999999999.99
    },
    "from_account": {
      "type": "string",
      "description": "Source account name or ID (money flows FROM this account)"
    },
    "to_account": {
      "type": "string",
      "description": "Destination account name or ID (money flows TO this account)"
    },
    "description": {
      "type": "string",
      "description": "Brief description of the transaction",
      "minLength": 1,
      "maxLength": 255
    },
    "date": {
      "type": "string",
      "format": "date",
      "description": "Transaction date in YYYY-MM-DD format (defaults to today)"
    },
    "notes": {
      "type": "string",
      "description": "Additional notes (optional)",
      "maxLength": 500
    },
    "ledger_id": {
      "type": "string",
      "format": "uuid",
      "description": "Target ledger ID (required if user has multiple ledgers)"
    }
  },
  "required": ["amount", "from_account", "to_account", "description"]
}
```

#### Success Response

```json
{
  "success": true,
  "data": {
    "transaction": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "date": "2026-01-11",
      "description": "午餐 - 便當",
      "amount": 85.0,
      "from_account": {
        "id": "...",
        "name": "現金"
      },
      "to_account": {
        "id": "...",
        "name": "餐飲"
      },
      "notes": null
    }
  },
  "message": "交易已建立：從「現金」支出 $85.00 至「餐飲」"
}
```

#### Error Responses

**Account Not Found**

```json
{
  "success": false,
  "error": {
    "code": "ACCOUNT_NOT_FOUND",
    "message": "找不到科目「早餐」",
    "suggestions": ["餐飲", "早午餐", "外食"],
    "available_accounts": [
      { "id": "...", "name": "餐飲", "type": "EXPENSE" },
      { "id": "...", "name": "交通", "type": "EXPENSE" }
    ]
  }
}
```

**Invalid Amount**

```json
{
  "success": false,
  "error": {
    "code": "INVALID_AMOUNT",
    "message": "金額必須為正數，且最多兩位小數"
  }
}
```

**Multiple Ledgers**

```json
{
  "success": false,
  "error": {
    "code": "LEDGER_REQUIRED",
    "message": "您有多個帳本，請指定 ledger_id",
    "available_ledgers": [
      { "id": "...", "name": "個人帳本" },
      { "id": "...", "name": "家庭帳本" }
    ]
  }
}
```

---

### 2. list_accounts

Lists all accounts with their current balances.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "ledger_id": {
      "type": "string",
      "format": "uuid",
      "description": "Target ledger ID (required if user has multiple ledgers)"
    },
    "type": {
      "type": "string",
      "enum": ["ASSET", "LIABILITY", "INCOME", "EXPENSE"],
      "description": "Filter by account type"
    },
    "include_zero_balance": {
      "type": "boolean",
      "default": true,
      "description": "Include accounts with zero balance"
    }
  }
}
```

#### Success Response

```json
{
  "success": true,
  "data": {
    "accounts": [
      {
        "id": "...",
        "name": "現金",
        "type": "ASSET",
        "balance": 15000.0,
        "parent_id": null,
        "depth": 1
      },
      {
        "id": "...",
        "name": "銀行存款",
        "type": "ASSET",
        "balance": 50000.0,
        "parent_id": null,
        "depth": 1
      },
      {
        "id": "...",
        "name": "餐飲",
        "type": "EXPENSE",
        "balance": 3500.0,
        "parent_id": null,
        "depth": 1
      }
    ],
    "summary": {
      "total_assets": 65000.0,
      "total_liabilities": 0.0,
      "total_income": 50000.0,
      "total_expenses": 8500.0
    }
  },
  "message": "找到 12 個科目"
}
```

---

### 3. get_account

Gets detailed information about a specific account.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "account": {
      "type": "string",
      "description": "Account name or ID"
    },
    "ledger_id": {
      "type": "string",
      "format": "uuid",
      "description": "Target ledger ID (required if user has multiple ledgers)"
    }
  },
  "required": ["account"]
}
```

#### Success Response

```json
{
  "success": true,
  "data": {
    "account": {
      "id": "...",
      "name": "現金",
      "type": "ASSET",
      "balance": 15000.0,
      "parent_id": null,
      "depth": 1,
      "is_system": false,
      "children": [],
      "recent_transactions": [
        {
          "id": "...",
          "date": "2026-01-11",
          "description": "午餐",
          "amount": -85.0
        },
        {
          "id": "...",
          "date": "2026-01-10",
          "description": "提款",
          "amount": 3000.0
        }
      ]
    }
  },
  "message": "「現金」餘額為 $15,000.00"
}
```

---

### 4. list_transactions

Queries transaction history with optional filters.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "ledger_id": {
      "type": "string",
      "format": "uuid",
      "description": "Target ledger ID (required if user has multiple ledgers)"
    },
    "account_id": {
      "type": "string",
      "format": "uuid",
      "description": "Filter by account ID"
    },
    "account_name": {
      "type": "string",
      "description": "Filter by account name"
    },
    "start_date": {
      "type": "string",
      "format": "date",
      "description": "Start date (inclusive) in YYYY-MM-DD format"
    },
    "end_date": {
      "type": "string",
      "format": "date",
      "description": "End date (inclusive) in YYYY-MM-DD format"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 20,
      "description": "Maximum number of transactions to return"
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "default": 0,
      "description": "Number of transactions to skip"
    }
  }
}
```

#### Success Response

```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": "...",
        "date": "2026-01-11",
        "description": "午餐 - 便當",
        "amount": 85.0,
        "from_account": { "id": "...", "name": "現金" },
        "to_account": { "id": "...", "name": "餐飲" },
        "notes": null
      }
    ],
    "pagination": {
      "total": 150,
      "limit": 20,
      "offset": 0,
      "has_more": true
    },
    "summary": {
      "total_amount": 8500.0,
      "transaction_count": 45
    }
  },
  "message": "找到 150 筆交易（顯示第 1-20 筆）"
}
```

---

### 5. list_ledgers

Lists all ledgers available to the authenticated user.

#### Input Schema

```json
{
  "type": "object",
  "properties": {}
}
```

#### Success Response

```json
{
  "success": true,
  "data": {
    "ledgers": [
      {
        "id": "...",
        "name": "個人帳本",
        "description": "日常開銷記錄",
        "account_count": 12,
        "transaction_count": 150
      },
      {
        "id": "...",
        "name": "家庭帳本",
        "description": "家庭共同支出",
        "account_count": 8,
        "transaction_count": 45
      }
    ],
    "default_ledger_id": "..."
  },
  "message": "您有 2 個帳本"
}
```

---

## Common Error Codes

| Code                | HTTP Status | Description                                |
| ------------------- | ----------- | ------------------------------------------ |
| `UNAUTHORIZED`      | 401         | Invalid or missing API token               |
| `TOKEN_REVOKED`     | 401         | API token has been revoked                 |
| `LEDGER_NOT_FOUND`  | 404         | Specified ledger does not exist            |
| `LEDGER_REQUIRED`   | 400         | Multiple ledgers exist, ledger_id required |
| `ACCOUNT_NOT_FOUND` | 404         | Specified account does not exist           |
| `INVALID_AMOUNT`    | 400         | Amount validation failed                   |
| `INVALID_DATE`      | 400         | Date format or range invalid               |
| `VALIDATION_ERROR`  | 400         | General input validation error             |
| `INTERNAL_ERROR`    | 500         | Unexpected server error                    |

## MCP Tool Metadata

Each tool includes metadata for AI assistants:

```python
@mcp.tool(
    name="create_transaction",
    description="建立一筆新的記帳交易。例如：記錄午餐花費 85 元，從現金支出到餐飲科目。",
    annotations=ToolAnnotations(
        readOnlyHint=False,  # This tool modifies data
        destructiveHint=False,  # Does not delete data
        idempotentHint=False  # Calling twice creates two transactions
    )
)
```
