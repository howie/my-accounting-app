# Contributing Guide

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy
- **Frontend**: TypeScript 5.x, React, Vite
- **Database**: PostgreSQL 16 (via Docker)

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (Python package manager)

## Quick Start

### 1. Start Development Environment

```bash
# Full stack (recommended)
make dev-run

# Or start services separately:
make dev-db        # Start PostgreSQL (Docker)
make dev-backend   # Start FastAPI server
make dev-frontend  # Start Vite dev server
```

### 2. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3. Stop Services

```bash
make dev-stop
```

## Project Structure

```
my-accounting-app/
├── backend/           # FastAPI backend
│   ├── src/
│   │   ├── api/       # API routes
│   │   ├── models/    # SQLAlchemy models
│   │   └── services/  # Business logic
│   └── tests/
├── frontend/          # React frontend
│   └── src/
│       ├── components/
│       ├── pages/
│       └── services/
├── docs/
│   ├── features/      # Feature specifications
│   └── myab-spec/     # Product requirements
└── src/myab/          # Legacy desktop app
```

## Development Workflow

### Running Tests

```bash
# Backend tests
make test

# Frontend tests
cd frontend && npm test
```

### Linting

```bash
# Backend (ruff)
make lint

# Frontend (eslint)
cd frontend && npm run lint
```

### Pre-commit Hooks

This project uses pre-commit for code quality. Install hooks:

```bash
pip install pre-commit
pre-commit install
```

## Feature Development

This project uses **Spec-Driven Development**. See [CLAUDE.md](CLAUDE.md) for details.

### Creating a New Feature

1. Create feature spec: `/speckit.specify "feature description"`
2. Plan implementation: `/speckit.plan`
3. Generate tasks: `/speckit.tasks`

Feature docs are stored in `docs/features/###-feature-name/`.

## Code Style

- **Python**: Follow PEP 8, enforced by ruff
- **TypeScript**: Follow ESLint + Prettier config
- **Commits**: Use conventional commits format

## Getting Help

- Check existing [feature specs](docs/features/) for implementation details
- Review [product spec](docs/myab-spec/) for business requirements
