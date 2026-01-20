# Analyze Test Failures

You are tasked with analyzing test failures and determining if they can be auto-fixed.

## Project Structure

- `backend/` - Python tests (uses pytest)
- `frontend/` - TypeScript/React tests (uses jest/vitest)

## Steps

### 1. Capture Test Failures

Run tests to capture failures:

**Backend (pytest):**

```bash
cd backend && pytest -v --tb=short 2>&1 | head -200
```

**Frontend (if applicable):**

```bash
cd frontend && npm test -- --verbose 2>&1 | head -200
```

### 2. Categorize Failures

**Simple (Auto-fixable):**

- Import errors (missing imports)
- Syntax errors in test files
- Missing fixtures
- Outdated mock configurations

**Medium (May be fixable):**

- Test setup issues
- Mock return value mismatches
- Fixture configuration errors

**Complex (Require manual review):**

- Business logic errors
- Integration test failures
- Race conditions
- Data integrity issues

### 3. For Simple Failures

Apply fixes directly:

```python
# Fix missing imports
from module import needed_function

# Fix outdated assertions
assert result == expected_value
```

Then commit:

```bash
git add -A
git commit -m "fix: resolve test import/syntax errors [claude-agent]"
```

### 4. For Medium/Complex Failures

Create a detailed analysis report. Do NOT attempt to fix business logic errors.

## Output Format for Complex Issues

Create a PR comment with this format:

```markdown
## Test Failure Analysis

### Summary

X tests failed across Y test files

### Failed Tests

#### backend/tests/test_transactions.py::test_create_transaction

**Error**: AssertionError: expected balance 1000.00, got 999.99
**Root Cause**: Possible decimal rounding issue in balance calculation
**Suggested Fix**: Review decimal precision in `services/transaction_service.py`
**Severity**: Medium

#### backend/tests/test_accounts.py::test_account_hierarchy

**Error**: KeyError: 'parent_id'
**Root Cause**: Missing field in response serialization
**Suggested Fix**: Check AccountSchema in `schemas/account.py`
**Severity**: Low

### Recommendations

1. Review decimal handling in financial calculations
2. Verify schema completeness for nested objects
3. Add integration test for account hierarchy

### Files to Review

- backend/src/services/transaction_service.py
- backend/src/schemas/account.py
```

## Constraints

- Only auto-fix simple import/syntax errors
- Do NOT change test logic or assertions
- Do NOT modify business logic to make tests pass
- Do NOT delete or skip failing tests
- Provide detailed analysis for manual review
- Always preserve test intent and coverage
