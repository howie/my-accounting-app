.PHONY: all deps test lint build deploy clean dev-run help

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

dev-run: deps
	@echo "Starting application..."
	PYTHONPATH=src $(PYTHON) -m myab.main

help:
	@echo "Available commands:"
	@echo "  make deps      - Install dependencies using uv"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Run linter"
	@echo "  make build     - Build package"
	@echo "  make dev-run   - Run application in development mode"
	@echo "  make clean     - Clean up"
