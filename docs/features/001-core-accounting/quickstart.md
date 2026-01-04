# Quickstart: LedgerOne Core Accounting System

**Date**: 2026-01-02 (Updated from 2025-11-22)
**Feature**: Core Accounting System

This guide provides instructions for setting up and running the LedgerOne accounting application with the new Next.js + FastAPI + PostgreSQL architecture.

## Prerequisites

- **Docker** and **Docker Compose** (recommended for easy setup)
- Or manually install:
  - Python 3.12+
  - Node.js 20+
  - PostgreSQL 16+

## Quick Start with Docker

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/my-accounting-app.git
cd my-accounting-app

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Manual Setup

### 1. Database Setup

Start PostgreSQL locally or use a hosted service:

```bash
# Using Docker for just PostgreSQL
docker run -d \
  --name ledgerone-db \
  -e POSTGRES_USER=ledgerone \
  -e POSTGRES_PASSWORD=ledgerone \
  -e POSTGRES_DB=ledgerone \
  -p 5432:5432 \
  postgres:16

# Create .env file
cat > backend/.env << EOF
DATABASE_URL=postgresql://ledgerone:ledgerone@localhost:5432/ledgerone
EOF
```

### 2. Backend Setup

```bash
cd backend

# Using uv (recommended - faster)
uv sync
uv run uvicorn src.api.main:app --reload --port 8000

# Or using pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn src.api.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
EOF

# Start the development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## First-Time Setup

When you first open the application:

1. **User Setup**: You'll be redirected to `/setup` to create your user account
2. **Create Ledger**: After setup, create your first ledger (e.g., "Personal 2026")
3. **Add Accounts**: The system creates Cash and Equity accounts automatically. Add custom accounts (Groceries, Salary, etc.)
4. **Record Transactions**: Start recording your income, expenses, and transfers

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests (using uv)
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/contract/
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm run test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

## Project Structure

```
my-accounting-app/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── main.py           # FastAPI app entry
│   │   │   ├── deps.py           # Dependency injection
│   │   │   └── routes/           # API endpoints
│   │   ├── models/               # SQLModel entities
│   │   ├── services/             # Business logic
│   │   ├── db/                   # Database session & migrations
│   │   └── core/                 # Config & exceptions
│   ├── tests/
│   ├── alembic.ini
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── app/                  # Next.js App Router pages
│   │   ├── components/           # React components
│   │   ├── lib/                  # API client & utilities
│   │   └── types/                # TypeScript types
│   ├── tests/
│   ├── package.json
│   └── next.config.js
│
├── docs/
│   └── features/
│       └── 001-core-accounting/  # Feature documentation
│
└── docker-compose.yml
```

## API Documentation

Once the backend is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Common Tasks

### Create a New Ledger

```bash
curl -X POST http://localhost:8000/api/v1/ledgers \
  -H "Content-Type: application/json" \
  -d '{"name": "Personal 2026", "initial_balance": 10000}'
```

### List Accounts

```bash
curl http://localhost:8000/api/v1/ledgers/{ledger_id}/accounts
```

### Create a Transaction

```bash
curl -X POST http://localhost:8000/api/v1/ledgers/{ledger_id}/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-01-02",
    "description": "Grocery shopping",
    "amount": 50.00,
    "from_account_id": "{cash_account_id}",
    "to_account_id": "{expense_account_id}",
    "transaction_type": "EXPENSE"
  }'
```

## Development Workflow

1. **Make changes** to backend or frontend code
2. **Run tests** to ensure nothing is broken
3. **Check API docs** at `/docs` for endpoint verification
4. **Commit changes** following conventional commit format

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check connection
psql -h localhost -U ledgerone -d ledgerone

# Reset database
alembic downgrade base
alembic upgrade head
```

### Frontend Build Issues

```bash
# Clear Next.js cache
rm -rf frontend/.next

# Reinstall dependencies
rm -rf frontend/node_modules
npm install
```

### Port Conflicts

If ports 3000, 8000, or 5432 are in use:

```bash
# Find process using port
lsof -i :3000

# Change ports in docker-compose.yml or .env files
```
