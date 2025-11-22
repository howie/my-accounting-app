# Quickstart Guide: Core Accounting

**Feature**: 001-core-accounting

## Prerequisites

- Python 3.11+
- Git

## Setup

1. **Clone and Navigate**:
   ```bash
   git clone [repo-url]
   cd my-accounting-app
   ```

2. **Create Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\Scripts\activate   # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Running Tests

We use TDD. Run tests frequently.

```bash
pytest                    # Run all tests
pytest tests/unit         # Run unit tests
pytest tests/integration  # Run integration tests
pytest --cov=src/myab     # Check coverage
```

## Project Structure

- `src/myab/models`: Data classes (UserAccount, Ledger, Account, Transaction)
- `src/myab/persistence`: Database access (Repositories)
- `src/myab/services`: Business logic (Double-entry rules)
- `src/myab/ui`: GUI components (tkinter)

## Development Workflow

1. **Pick a Task**: Check `docs/features/001-core-accounting/tasks.md`
2. **Write a Test**: Create a failing test in `tests/`
3. **Implement**: Write code in `src/` to pass the test
4. **Refactor**: Clean up code
5. **Commit**: Use descriptive messages

## Database

- SQLite file is created at `myab.db` (default) or specified path.
- Schema is defined in `src/myab/persistence/schema.sql`.
- Use `sqlite3` CLI to inspect data: `sqlite3 myab.db`
