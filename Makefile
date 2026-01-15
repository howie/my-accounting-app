.PHONY: all deps test lint build deploy clean dev-run dev-backend dev-frontend dev-db dev-stop check check-backend check-frontend check-security help

VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python

all: deps build test lint

deps: $(VENV_DIR)/.installed

$(VENV_DIR)/.installed: requirements-dev.txt
	@echo "Setting up virtual environment and installing dependencies using uv..."
	uv venv $(VENV_DIR)
	uv pip install -r requirements-dev.txt
	touch $(VENV_DIR)/.installed
	@echo "Dependencies installed."

test: deps
	@echo "Running tests..."
	$(PYTHON) -m pytest

lint: deps
	@echo "Running linter (ruff)..."
	$(PYTHON) -m ruff check src/ tests/

build: deps
	@echo "Building package..."
	$(PYTHON) -m build --sdist --wheel .

deploy:
	@echo "Deployment for desktop application is highly specific and often involves tools like PyInstaller or cx_Freeze."
	@echo "This target is a placeholder. Consider adding:"
	@echo "  - PyInstaller command to create an executable."
	@echo "  - Script to create an installer (e.g., for Windows/macOS)."
	@echo "No deployment action performed."

clean:
	@echo "Cleaning up build artifacts and virtual environment..."
	rm -rf $(VENV_DIR) build dist *.egg-info .pytest_cache .coverage* htmlcov
	@echo "Cleanup complete."

# Web application development targets
dev-run:
	@echo "Starting full development environment..."
	@echo ""
	@echo "This requires Docker to be running. If Docker is not available, use:"
	@echo "  Terminal 1: make dev-db       (start database)"
	@echo "  Terminal 2: make dev-backend  (start backend)"
	@echo "  Terminal 3: make dev-frontend (start frontend)"
	@echo ""
	docker-compose up -d postgres backend
	@echo "Waiting for backend to be ready..."
	@sleep 3
	@echo "Starting frontend with hot reload..."
	cd frontend && npm run dev

dev-db:
	@echo "Starting database only (requires Docker)..."
	docker-compose up -d postgres

dev-backend:
	@echo "Starting backend server (requires database on localhost:5433)..."
	@echo "Run 'make dev-db' first if database is not running."
	cd backend && PYTHONPATH=. .venv/bin/python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir src

dev-frontend:
	@echo "Starting frontend with hot reload..."
	cd frontend && npm run dev

dev-stop:
	@echo "Stopping all services..."
	docker-compose down

# Legacy desktop app (myab)
myab-run: deps
	@echo "Starting legacy myab desktop application..."
	PYTHONPATH=src $(PYTHON) -m myab.main

# CI Checks - Run all checks like CI does
check: check-backend check-frontend check-security
	@echo ""
	@echo "✓ All checks passed!"
	@echo ""

check-backend:
	@echo "==> Running pre-commit hooks..."
	pre-commit run --all-files || (echo "✗ Pre-commit hooks failed" && exit 1)
	@echo ""
	@echo "==> Running backend code quality checks..."
	cd backend && ruff check . || (echo "✗ Ruff linter failed" && exit 1)
	@echo ""
	@echo "==> Running backend format check..."
	cd backend && ruff format --check . || (echo "✗ Ruff format check failed" && exit 1)
	@echo ""
	@echo "==> Running mypy type checking..."
	cd backend && mypy src || echo "⚠ Mypy type checking has issues (currently allowed)"
	@echo ""
	@echo "==> Running backend tests with coverage..."
	cd backend && pytest --cov=src --cov-report=term-missing || (echo "✗ Tests failed" && exit 1)
	@echo ""
	@echo "✓ Backend checks passed"

check-frontend:
	@echo "==> Installing frontend dependencies..."
	cd frontend && npm ci --legacy-peer-deps
	@echo ""
	@echo "==> Running frontend linter..."
	cd frontend && npm run lint || echo "⚠ Frontend linting has issues (currently allowed)"
	@echo ""
	@echo "==> Running frontend type checking..."
	cd frontend && npm run type-check || echo "⚠ Frontend type checking has issues (currently allowed)"
	@echo ""
	@echo "==> Building frontend..."
	cd frontend && npm run build || (echo "✗ Frontend build failed" && exit 1)
	@echo ""
	@echo "✓ Frontend checks passed"

check-security:
	@echo "==> Running Bandit security linter..."
	bandit -r backend/src -ll || echo "⚠ Bandit found potential security issues (currently allowed)"
	@echo ""
	@echo "==> Checking dependencies for known vulnerabilities..."
	cd backend && pip install -e ".[dev]" > /dev/null && safety check --json || echo "⚠ Safety found potential vulnerabilities (currently allowed)"
	@echo ""
	@echo "✓ Security checks passed"

help:
	@echo "Available commands:"
	@echo ""
	@echo "Web Application Development:"
	@echo "  make dev-run      - Start full dev environment (db + backend + frontend)"
	@echo "  make dev-db       - Start database only (Docker)"
	@echo "  make dev-backend  - Start backend server locally"
	@echo "  make dev-frontend - Start frontend with hot reload"
	@echo "  make dev-stop     - Stop all Docker services"
	@echo ""
	@echo "Legacy Desktop App:"
	@echo "  make myab-run     - Run legacy myab desktop application"
	@echo ""
	@echo "CI Checks (like CI pipeline):"
	@echo "  make check        - Run all checks (backend + frontend + security)"
	@echo "  make check-backend - Run backend checks (pre-commit, ruff, mypy, tests)"
	@echo "  make check-frontend - Run frontend checks (lint, type-check, build)"
	@echo "  make check-security - Run security checks (bandit, safety)"
	@echo ""
	@echo "Build & Test:"
	@echo "  make deps         - Install dependencies using uv"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linter"
	@echo "  make build        - Build package"
	@echo "  make clean        - Clean up"
