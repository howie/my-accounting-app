# Fix Type Errors

You are tasked with fixing type checking errors in the codebase. This project uses mypy for Python and TypeScript for frontend.

## Project Structure

- `backend/` - Python code (uses mypy for type checking)
- `frontend/` - TypeScript/React code (uses tsc for type checking)

## Steps

### 1. Capture Type Errors

Run type checkers to capture current errors:

**Backend (Python/mypy):**

```bash
cd backend && mypy src --show-error-codes --pretty
```

**Frontend (TypeScript):**

```bash
cd frontend && npm run type-check
```

### 2. Analyze Errors

Categorize errors by type:

- **Missing type annotations**: Function parameters or return types not annotated
- **Incompatible types**: Type mismatch in assignments or function calls
- **Missing imports**: Type imports not present
- **Optional type issues**: Possible None values not handled
- **Generic type issues**: Incorrect generic type parameters

### 3. Apply Fixes

For each error, apply the appropriate fix:

**Missing annotations:**

```python
# Before
def calculate_total(items):
    return sum(items)

# After
def calculate_total(items: list[float]) -> float:
    return sum(items)
```

**Optional type handling:**

```python
# Before
def get_name(user):
    return user.name

# After
def get_name(user: User | None) -> str | None:
    return user.name if user else None
```

**TypeScript fixes:**

```typescript
// Add proper types to function parameters
// Use proper generic types
// Add null checks where needed
```

### 4. Verify Fixes

Run type checkers again:

```bash
cd backend && mypy src
cd frontend && npm run type-check
```

### 5. Commit Changes

```bash
git add -A
git commit -m "fix: resolve type errors [claude-agent]

- Added missing type annotations
- Fixed type incompatibilities
- Resolved mypy/TypeScript errors"
```

## Constraints

- Prefer explicit types over `Any`
- Use modern Python typing syntax (list[str] not List[str])
- Follow project type conventions (check existing code)
- Do NOT suppress errors with `# type: ignore` unless absolutely necessary
- Prefer `| None` over `Optional[]` for Python 3.10+
- Add type imports from `typing` module when needed
