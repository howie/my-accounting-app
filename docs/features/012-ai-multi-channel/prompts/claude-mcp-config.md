# Claude MCP Server Configuration

## Overview

Claude connects to LedgerOne via MCP (Model Context Protocol). The MCP server is already implemented in Feature 007 and provides the following tools:

- `create_transaction` — 建立交易
- `list_transactions` — 查詢交易
- `list_accounts` — 列出帳戶
- `list_ledgers` — 列出帳本
- `get_account_balance` — 查詢帳戶餘額

## Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ledgerone": {
      "url": "{YOUR_API_URL}/mcp",
      "headers": {
        "Authorization": "Bearer {YOUR_API_TOKEN}"
      }
    }
  }
}
```

## Authentication

- Method: Bearer Token in MCP request headers
- Token from: LedgerOne Settings > API Tokens
- The MCP server validates tokens via `ApiTokenService`

## No Additional Changes Needed

The existing MCP server (Feature 007) already supports all operations needed for US1. Claude can use the MCP tools directly with the API token for authentication.
