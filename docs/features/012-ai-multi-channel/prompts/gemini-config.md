# Gemini Extension Configuration

## Overview

Gemini can connect to LedgerOne via REST API using Function Declarations or Extensions.

## Function Declarations

Gemini Extensions use function declarations to define available actions. Map these to the LedgerOne REST API:

### createTransaction

```json
{
  "name": "createTransaction",
  "description": "建立一筆記帳交易",
  "parameters": {
    "type": "object",
    "properties": {
      "amount": { "type": "number", "description": "金額" },
      "from_account": { "type": "string", "description": "來源帳戶名稱" },
      "to_account": { "type": "string", "description": "目的帳戶名稱" },
      "description": { "type": "string", "description": "交易描述" },
      "date": { "type": "string", "description": "日期 YYYY-MM-DD，預設今天" }
    },
    "required": ["amount", "from_account", "to_account", "description"]
  }
}
```

### listTransactions

```json
{
  "name": "listTransactions",
  "description": "查詢交易紀錄",
  "parameters": {
    "type": "object",
    "properties": {
      "start_date": { "type": "string", "description": "開始日期 YYYY-MM-DD" },
      "end_date": { "type": "string", "description": "結束日期 YYYY-MM-DD" },
      "account_name": { "type": "string", "description": "篩選帳戶名稱" },
      "limit": { "type": "integer", "description": "最多回傳筆數，預設 20" }
    }
  }
}
```

### listAccounts

```json
{
  "name": "listAccounts",
  "description": "列出所有帳戶",
  "parameters": {
    "type": "object",
    "properties": {
      "type": {
        "type": "string",
        "description": "帳戶類型篩選：ASSET/LIABILITY/INCOME/EXPENSE"
      }
    }
  }
}
```

## Authentication

- Method: Bearer Token
- Header: `Authorization: Bearer {API_TOKEN}`
- Token from: LedgerOne Settings > API Tokens

## API Base URL

```
{YOUR_API_URL}/api/v1
```
