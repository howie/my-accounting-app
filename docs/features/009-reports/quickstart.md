# Quickstart: Testing Reports

**Feature**: 009-reports

## Prerequisites

- Backend running: `cd backend && uv run uvicorn src.api.main:app --reload`
- Frontend running: `cd frontend && npm run dev`

## 1. Verify API Endpoints (Backend)

Use `curl` or Postman to check the new endpoints.

### Balance Sheet

```bash
curl "http://localhost:8000/api/v1/reports/balance-sheet?date=2026-01-16"
```

**Expected Output**: JSON with `assets`, `liabilities`, `equity` and totals.

### Income Statement

```bash
curl "http://localhost:8000/api/v1/reports/income-statement?start_date=2026-01-01&end_date=2026-01-31"
```

**Expected Output**: JSON with `income`, `expenses` and `net_income`.

## 2. Verify Frontend Pages

1.  Navigate to `http://localhost:3000/reports/balance-sheet`.
2.  Check that the date picker defaults to today.
3.  Verify the "Assets" and "Liabilities" sections match your known data.
4.  Navigate to `http://localhost:3000/reports/income-statement`.
5.  Check that the date range defaults to current month.
6.  Verify the "Net Income" calculation.

## 3. Automated Tests

Run backend tests:

```bash
cd backend
uv run pytest tests/unit/services/test_report_service.py
uv run pytest tests/contract/api/test_reports.py
```
