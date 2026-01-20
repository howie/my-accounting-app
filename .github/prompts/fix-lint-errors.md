# Fix Lint Errors

You are tasked with fixing linting errors in the codebase. This project has both Python (backend) and TypeScript (frontend) code.

## Project Structure

- `backend/` - Python code (uses ruff for linting)
- `frontend/` - TypeScript/React code (uses eslint for linting)

## Steps

### 1. Identify and Capture Errors

Run the linters to capture current errors:

**Backend (Python):**

```bash
cd backend && ruff check . --output-format=text
```

**Frontend (TypeScript):**

```bash
cd frontend && npm run lint
```

### 2. Apply Auto-Fixes

Try automatic fixes first:

**Backend:**

```bash
cd backend && ruff check --fix . && ruff format .
```

**Frontend:**

```bash
cd frontend && npm run lint -- --fix
```

### 3. Manual Fixes

For errors that cannot be auto-fixed:

1. Read the file containing the error
2. Understand the context
3. Apply the appropriate fix using the Edit tool
4. Common fixes:
   - **E501 (line too long)**: Break long lines
   - **F401 (unused import)**: Remove the import
   - **F841 (unused variable)**: Remove or use the variable
   - **@typescript-eslint/no-unused-vars**: Remove unused variables
   - **import/order**: Reorder imports

### 4. Verify Fixes

Run linters again to confirm all errors are resolved:

```bash
cd backend && ruff check .
cd frontend && npm run lint
```

### 5. Commit Changes

```bash
git add -A
git commit -m "style: auto-fix lint errors [claude-agent]

- Fixed ruff errors in backend
- Fixed eslint errors in frontend
- Applied formatting corrections"
```

## Constraints

- Only fix lint and formatting issues
- Do NOT change logic or functionality
- Do NOT modify test files unless lint errors exist there
- Respect existing code style and patterns from CLAUDE.md
- Python: 100 char line length, double quotes, 4-space indent
- TypeScript: single quotes, semicolons, 2-space indent
