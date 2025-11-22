.PHONY: all deps test lint build deploy clean

VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip

all: deps build test lint

deps: $(VENV_DIR)/.installed

$(VENV_DIR)/.installed: requirements-dev.txt
	@echo "Setting up virtual environment and installing dependencies..."
	python3 -m venv $(VENV_DIR)
	$(PIP) install -U pip
	$(PIP) install -r requirements-dev.txt
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
