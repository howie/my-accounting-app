.PHONY: all deps test lint build deploy clean dev-run dev-backend dev-frontend dev-db dev-stop help

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
	cd backend && PYTHONPATH=. .venv/bin/python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir src

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
	@echo "Build & Test:"
	@echo "  make deps         - Install dependencies using uv"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linter"
	@echo "  make build        - Build package"
	@echo "  make clean        - Clean up"
