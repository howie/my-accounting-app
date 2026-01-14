# CI/CD Configuration

This directory contains GitHub Actions workflows and CI/CD configuration for the project.

## Workflows

### CI Workflow (`ci.yml`)

Comprehensive continuous integration workflow that runs on:

- Push to `main` branch
- Push to any `claude/**` branch
- Pull requests to `main` branch

#### Jobs

1. **Pre-commit Hooks**
   - Runs all pre-commit hooks defined in `.pre-commit-config.yaml`
   - Ensures code quality and consistency

2. **Backend Code Quality**
   - Ruff linter check
   - Ruff formatter check
   - mypy type checking

3. **Backend Tests**
   - Full pytest suite with coverage
   - PostgreSQL 16 service for integration tests
   - Coverage reports uploaded to Codecov

4. **Frontend Code Quality**
   - ESLint checks
   - TypeScript type checking
   - Build verification

5. **Security Checks**
   - Bandit security linter
   - Safety dependency vulnerability scanning

## Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality before commits.

### Setup

Install pre-commit hooks locally:

```bash
pip install pre-commit
pre-commit install
```

### Running Hooks

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Update hooks to latest versions
pre-commit autoupdate
```

### Configured Hooks

- **File checks**: trailing whitespace, end-of-file, YAML/JSON validation
- **Ruff**: Python linting and formatting
- **mypy**: Type checking for backend code
- **Bandit**: Security vulnerability scanning
- **Safety**: Dependency vulnerability checking
- **Prettier**: Frontend code formatting

## Type Checking with mypy

The backend uses strict mypy type checking. Configuration is in `backend/pyproject.toml`.

### Running mypy locally

```bash
cd backend
mypy src
```

### mypy Configuration

- Strict mode enabled
- Python 3.12 target
- Pydantic plugin enabled
- Test files have relaxed type checking

## Testing

### Backend Tests

```bash
cd backend
pytest --cov=src --cov-report=term-missing
```

### With PostgreSQL

The tests require PostgreSQL. Use Docker:

```bash
docker run -d \
  --name test-postgres \
  -e POSTGRES_USER=testuser \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=testdb \
  -p 5432:5432 \
  postgres:16
```

## Continuous Integration

All CI checks must pass before merging:

- Pre-commit hooks
- Backend code quality (Ruff, mypy)
- Backend tests with coverage
- Frontend build

Optional checks (won't block CI):

- Frontend linting
- Security scans

## Troubleshooting

### Pre-commit hooks failing

1. Run hooks manually to see detailed errors:

   ```bash
   pre-commit run --all-files --verbose
   ```

2. Fix any reported issues

3. Re-commit

### mypy errors

1. Ensure you have the latest dependencies:

   ```bash
   cd backend
   pip install -e ".[dev]"
   ```

2. Run mypy locally to see full error messages:
   ```bash
   mypy src --show-error-codes
   ```

### CI failing on GitHub

1. Check the Actions tab for detailed logs
2. Reproduce the issue locally using the same commands from the workflow
3. Ensure all dependencies are up to date
