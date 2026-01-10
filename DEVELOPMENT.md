# Development Guide

This document covers how to set up, develop, and test LedgerOne locally.

## Prerequisites

- **Python 3.12+** (managed via asdf or pyenv)
- **Node.js 20+** (managed via asdf or nvm)
- **Docker & Docker Compose** (for PostgreSQL)
- **uv** (Python package manager) - `pip install uv`

## Environment Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/howie/my-accounting-app.git
cd my-accounting-app

# Backend dependencies
cd backend
uv venv .venv
uv pip install -e ".[dev]"

# Frontend dependencies
cd ../frontend
npm install
```

### 2. Database Setup

```bash
# Start PostgreSQL with Docker
make dev-db

# Or use docker-compose directly
docker-compose up -d postgres
```

The database will be available at `localhost:5433` with:

- Database: `ledgerone`
- User: `ledgerone`
- Password: `ledgerone`

### 3. Run Migrations

```bash
cd backend
uv run alembic upgrade head
```

### 4. Environment Variables

Create `.env` files if needed:

```bash
# backend/.env
DATABASE_URL=postgresql://ledgerone:ledgerone@localhost:5433/ledgerone

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development Workflow

### Start All Services

```bash
# Recommended: Start everything with one command
make dev-run
```

### Or Start Services Individually

```bash
# Terminal 1: Database
make dev-db

# Terminal 2: Backend (http://localhost:8000)
make dev-backend

# Terminal 3: Frontend (http://localhost:3000)
make dev-frontend
```

### Available Make Commands

| Command             | Description                          |
| ------------------- | ------------------------------------ |
| `make dev-run`      | Start full dev environment           |
| `make dev-db`       | Start PostgreSQL only                |
| `make dev-backend`  | Start FastAPI server with hot reload |
| `make dev-frontend` | Start Next.js dev server             |
| `make dev-stop`     | Stop all Docker services             |
| `make test`         | Run legacy tests                     |
| `make lint`         | Run linter                           |
| `make clean`        | Clean up build artifacts             |

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/test_csv_parser.py

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with watch mode
npm run test:watch
```

### Pre-commit Hooks

The project uses pre-commit for code quality:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Hooks include:

- **ruff** - Python linting and formatting
- **prettier** - JavaScript/TypeScript formatting
- **bandit** - Python security checks

## Code Quality

### Backend (Python)

```bash
cd backend

# Linting
uv run ruff check .

# Auto-fix
uv run ruff check --fix .

# Format
uv run ruff format .
```

### Frontend (TypeScript)

```bash
cd frontend

# Linting
npm run lint

# Type checking
npm run type-check

# Format (via prettier)
npm run format
```

## Database Migrations

```bash
cd backend

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one step
uv run alembic downgrade -1
```

## API Documentation

When the backend is running, API docs are available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Feature Development

This project uses Spec-Driven Development. Feature specs are in `docs/features/`:

```
docs/features/
├── 001-core-accounting/
│   ├── spec.md      # Feature specification
│   ├── plan.md      # Implementation plan
│   ├── tasks.md     # Task breakdown
│   └── ...
├── 002-ui-layout-dashboard/
└── ...
```

### Creating a New Feature

Use the speckit CLI:

```bash
# Create feature spec
/speckit.specify "feature description"

# Create implementation plan
/speckit.plan

# Generate tasks
/speckit.tasks
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Port Conflicts

Default ports:

- PostgreSQL: 5433
- Backend: 8000
- Frontend: 3000

If ports are in use, modify `docker-compose.yml` or use environment variables.

### Dependency Issues

```bash
# Backend: Reinstall dependencies
cd backend
rm -rf .venv
uv venv .venv
uv pip install -e ".[dev]"

# Frontend: Clean install
cd frontend
rm -rf node_modules
npm install
```
