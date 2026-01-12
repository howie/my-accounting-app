# LedgerOne

A local-first, double-entry personal accounting system built with modern web technologies.

## Overview

LedgerOne is a personal finance management application that implements proper double-entry bookkeeping principles. It helps you track your assets, liabilities, income, and expenses across multiple ledgers with a clean, intuitive interface.

## Features

### Core Accounting

- **Multiple Ledgers** - Manage separate books for different purposes (personal, business, etc.)
- **Double-Entry Bookkeeping** - Every transaction has balanced debits and credits
- **Four Account Types** - Asset, Liability, Income, and Expense accounts
- **Hierarchical Accounts** - Support for up to 3 levels of nested sub-accounts
- **Transaction Management** - Record expenses, income, and transfers between accounts

### User Interface

- **Dashboard** - Visual overview with total assets, income vs expenses charts, and monthly trends
- **Sidebar Navigation** - Hierarchical account tree with collapsible categories
- **Account Management** - Create, edit, delete, and reorder accounts with drag-and-drop
- **Mobile Responsive** - Works on desktop and mobile devices
- **Dark/Light Mode** - Theme switching support
- **Internationalization** - Available in English and Traditional Chinese (zh-TW)

### Data Import (New)

- **Batch Import** - Import transactions from CSV files
- **MyAB CSV Support** - Import data from MyAB accounting software
- **Account Mapping** - Auto-match or create new accounts during import
- **Duplicate Detection** - Identify and skip duplicate transactions
- **Preview Before Import** - Review data before committing

### MCP API for AI Assistants (New)

- **AI-Powered Accounting** - Let Claude or other AI assistants help you record transactions
- **Natural Language Commands** - Say "Lunch cost $15" and AI creates the transaction
- **Query Support** - Ask "How much did I spend on food this month?"
- **Secure API Tokens** - Generate and manage tokens from the Settings page
- **Full MCP Protocol** - Compatible with Claude Desktop and other MCP clients

### Audit & Integrity

- **Audit Trail** - All account changes are logged
- **Data Validation** - Strict validation ensures data integrity
- **Atomic Transactions** - All-or-nothing imports prevent partial data

## Tech Stack

| Layer    | Technology                                     |
| -------- | ---------------------------------------------- |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend  | Python 3.12, FastAPI, SQLModel                 |
| Database | PostgreSQL 16                                  |
| MCP API  | FastMCP, Model Context Protocol                |
| Charts   | Tremor, Recharts                               |
| State    | TanStack Query                                 |
| i18n     | next-intl                                      |

## Quick Start

See [DEVELOPMENT.md](./DEVELOPMENT.md) for detailed setup instructions.

```bash
# Start with Docker (recommended)
make dev-run

# Or start services individually
make dev-db        # Start PostgreSQL
make dev-backend   # Start FastAPI server
make dev-frontend  # Start Next.js dev server
```

## MCP API Setup (AI Assistant Integration)

LedgerOne supports Model Context Protocol (MCP), allowing AI assistants like Claude Desktop to help manage your accounting.

### 1. Generate an API Token

1. Start LedgerOne and go to **Settings** → **API Tokens**
2. Click **Create Token** and give it a name (e.g., "Claude Desktop")
3. Copy the generated token (shown only once!)

### 2. Configure Claude Desktop

Edit your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ledgerone": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer ldo_your_token_here..."
      }
    }
  }
}
```

### 3. Start Using

Once connected, you can tell Claude things like:

- "Lunch was $12"
- "How much cash do I have?"
- "Show this week's expenses"

For detailed setup, see [docs/features/007-api-for-mcp/quickstart.md](./docs/features/007-api-for-mcp/quickstart.md).

## Project Structure

```
.
├── backend/          # FastAPI backend
│   ├── src/          # Source code
│   │   ├── api/      # API routes
│   │   ├── models/   # SQLModel models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   └── tests/        # Backend tests
├── frontend/         # Next.js frontend
│   ├── src/
│   │   ├── app/      # App router pages
│   │   ├── components/
│   │   └── lib/      # Utilities, hooks, API clients
│   └── messages/     # i18n translations
└── docs/             # Documentation
    └── features/     # Feature specifications
```

## Roadmap

See [docs/features/ROADMAP.md](./docs/features/ROADMAP.md) for planned features.

**Completed:**

- Core Accounting (001)
- UI Layout & Dashboard (002)
- Settings & Account Management (003)
- Transaction Entry with Templates (004)
- Data Import - MyAB CSV (006)
- MCP API for AI Assistants (007)

**Planned:**

- UI Navigation v2 (005)
- Reports - Balance Sheet, Income Statement (008)
- Advanced Transactions (009)
- Budget Management (010)

## License

[AGPL-3.0](./LICENSE)
