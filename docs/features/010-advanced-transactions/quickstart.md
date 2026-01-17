# Quickstart: Advanced Transactions

**Status**: Phase 1 Ready
**Branch**: `010-advanced-transactions`

## Prerequisites

- Backend running: `cd backend && uvicorn src.main:app --reload`
- Frontend running: `cd frontend && npm run dev`

## 1. Manage Tags

Tags allow you to categorize transactions with flexible labels.

```bash
# Create a tag
curl -X POST http://localhost:8000/api/v1/tags \
  -H "Content-Type: application/json" \
  -d '{"name": "Vacation", "color": "#FF5733"}'

# List tags
curl http://localhost:8000/api/v1/tags
```

## 2. Create Recurring Transaction

Set up a template for transactions that repeat.

```bash
# Create a monthly rent template
curl -X POST http://localhost:8000/api/v1/recurring \
  -H "Content-Type: application/json" \
  -d
  {
    "name": "Rent",
    "amount": 120000,
    "transaction_type": "EXPENSE",
    "frequency": "MONTHLY",
    "start_date": "2026-02-01",
    "source_account_id": "UUID_HERE",
    "dest_account_id": "UUID_HERE"
  }
```

## 3. Approve Due Transactions

Check for due recurring items and approve them.

```bash
# Check due items
curl http://localhost:8000/api/v1/recurring/due

# Approve specific instance
curl -X POST http://localhost:8000/api/v1/recurring/{recurring_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-02-01"}'
```

## 4. Create Installment Plan

Record a large purchase split over time.

```bash
# Create 12-month installment plan
curl -X POST http://localhost:8000/api/v1/installments \
  -H "Content-Type: application/json" \
  -d
  {
    "name": "New Laptop",
    "total_amount": 240000,
    "installment_count": 12,
    "source_account_id": "UUID_HERE",
    "dest_account_id": "UUID_HERE",
    "start_date": "2026-01-17"
  }
```

## Testing

Run specific tests for this feature:

```bash
# Backend
cd backend
pytest tests/unit/test_tag_service.py tests/unit/test_recurring_service.py tests/unit/test_installment_service.py
pytest tests/integration/test_tags_api.py tests/integration/test_recurring_flow.py tests/integration/test_installments.py

# Frontend
cd frontend
npm run test
```
