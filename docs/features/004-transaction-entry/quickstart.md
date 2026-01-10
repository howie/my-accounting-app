# Quickstart: Transaction Entry

**Feature**: 004-transaction-entry
**Date**: 2026-01-09

## Prerequisites

Before starting implementation, ensure:

1. **001-core-accounting** is complete (Transaction model exists)
2. **002-ui-layout-dashboard** is complete (Account pages exist)
3. **003-settings-account-management** is complete (Account hierarchy works)
4. Development environment is set up:
   - Backend: Python 3.12, PostgreSQL running
   - Frontend: Node.js 20+, dependencies installed

## Quick Validation Checklist

Use this checklist to validate the feature after implementation:

### Phase 1: Transaction Entry (P1)

- [ ] **Add Transaction Button**: Account page shows "Add Transaction" button
- [ ] **Modal Opens**: Clicking button opens modal dialog
- [ ] **Account Pre-selection**: Current account is pre-selected as From/To based on type
- [ ] **Transaction Type Auto-suggest**: Type auto-selects based on From account
- [ ] **Date Picker**: Can select dates, defaults to today
- [ ] **Amount Calculator**: Expression "50+40" calculates to 90
- [ ] **Description Required**: Cannot save without description
- [ ] **Save & Close**: Transaction saves and modal closes
- [ ] **List Refresh**: New transaction appears in list immediately

### Phase 2: Templates (P2)

- [ ] **Save as Template**: Can save transaction form as named template
- [ ] **Template List**: Can view all templates for ledger
- [ ] **Apply Template**: Applying template fills form (date stays today)
- [ ] **Quick Entry Panel**: Dashboard shows template buttons
- [ ] **Quick Save**: Can quick-save from template with confirmation

### Phase 3: Template Management (P3)

- [ ] **Edit Template**: Can modify existing template
- [ ] **Delete Template**: Can delete template with confirmation
- [ ] **Reorder Templates**: Can drag-drop to reorder

### Edge Cases

- [ ] **Zero Amount Warning**: Shows confirmation for $0 transactions
- [ ] **Same Account Error**: Blocks saving when From = To account
- [ ] **Max Templates**: Shows error at 50 templates
- [ ] **Deleted Account**: Template with deleted account shows error

## Development Commands

### Backend

```bash
# Navigate to backend
cd backend

# Run migrations
alembic upgrade head

# Start development server
uvicorn src.main:app --reload

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_template_service.py -v
```

### Frontend

```bash
# Navigate to frontend
cd frontend

# Start development server
npm run dev

# Run tests
npm run test

# Run specific test file
npm run test -- AmountInput.test.tsx
```

## API Endpoints Summary

| Method | Endpoint                                 | Description        |
| ------ | ---------------------------------------- | ------------------ |
| POST   | `/api/ledgers/{id}/transactions`         | Create transaction |
| GET    | `/api/ledgers/{id}/templates`            | List templates     |
| POST   | `/api/ledgers/{id}/templates`            | Create template    |
| GET    | `/api/ledgers/{id}/templates/{id}`       | Get template       |
| PATCH  | `/api/ledgers/{id}/templates/{id}`       | Update template    |
| DELETE | `/api/ledgers/{id}/templates/{id}`       | Delete template    |
| PATCH  | `/api/ledgers/{id}/templates/reorder`    | Reorder templates  |
| POST   | `/api/ledgers/{id}/templates/{id}/apply` | Apply template     |

## Key Files to Implement

### Backend (in order)

1. `src/models/transaction_template.py` - TransactionTemplate model
2. `src/schemas/transaction_template.py` - Pydantic schemas
3. `src/services/template_service.py` - Business logic
4. `src/api/routes/templates.py` - API endpoints
5. `alembic/versions/xxx_add_notes_and_templates.py` - Migration

### Frontend (in order)

1. `src/lib/utils/expressionParser.ts` - Amount calculator
2. `src/components/transactions/AmountInput.tsx` - Calculator input
3. `src/components/transactions/TransactionForm.tsx` - Form fields
4. `src/components/transactions/TransactionModal.tsx` - Modal wrapper
5. `src/lib/hooks/useTemplates.ts` - Template API hooks
6. `src/components/templates/QuickEntryPanel.tsx` - Dashboard panel

## Testing Strategy

### TDD Flow (per Constitution)

1. Write test first
2. Get test approval
3. Verify test fails
4. Implement feature
5. Verify test passes
6. Refactor

### Test Coverage Requirements

| Component          | Unit | Integration | Contract |
| ------------------ | ---- | ----------- | -------- |
| Expression Parser  | ✓    | -           | -        |
| Template Service   | ✓    | ✓           | -        |
| Transaction Create | ✓    | ✓           | ✓        |
| Template CRUD      | ✓    | ✓           | ✓        |
| AmountInput        | ✓    | -           | -        |
| TransactionModal   | ✓    | ✓           | -        |

## Common Issues & Solutions

### Expression Parser

**Issue**: Operator precedence incorrect
**Solution**: Use recursive descent parser with proper term/factor separation

### Modal Focus

**Issue**: Focus not trapped in modal
**Solution**: Use Radix Dialog which handles focus management

### Account Pre-selection

**Issue**: Wrong account pre-selected
**Solution**: Check account type: Asset/Expense → From, Income/Liability → To

### Template Foreign Key

**Issue**: "Account not found" when applying template
**Solution**: Template has ON DELETE RESTRICT - must update template first

## i18n Keys to Add

```json
{
  "transactions": {
    "addTransaction": "新增交易",
    "transactionType": "交易類型",
    "expense": "支出",
    "income": "收入",
    "transfer": "轉帳",
    "fromAccount": "從帳戶",
    "toAccount": "到帳戶",
    "amount": "金額",
    "date": "日期",
    "description": "描述",
    "notes": "備註",
    "save": "儲存",
    "cancel": "取消",
    "saveAsTemplate": "儲存為模板"
  },
  "templates": {
    "title": "交易模板",
    "quickEntry": "快速記帳",
    "templateName": "模板名稱",
    "apply": "套用",
    "edit": "編輯",
    "delete": "刪除",
    "confirmDelete": "確定要刪除此模板嗎？",
    "limitReached": "已達模板上限（50個）"
  },
  "validation": {
    "descriptionRequired": "請輸入交易描述",
    "sameAccountError": "來源與目的帳戶不能相同",
    "invalidExpression": "無效的計算式",
    "divideByZero": "無法除以零",
    "amountOutOfRange": "金額必須在 0.01 到 999,999,999.99 之間"
  }
}
```

## Next Steps

After completing this feature:

1. Run `/speckit.tasks` to generate detailed task breakdown
2. Follow TDD workflow for each task
3. Update ROADMAP.md to mark 004-transaction-entry as DONE
