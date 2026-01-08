# Quickstart: Settings & Account Management

**Feature**: 003-settings-account-management
**Date**: 2026-01-07
**Phase**: 1 - Design & Contracts

## Prerequisites

Before implementing this feature, ensure:

1. **001-core-accounting** is complete (Account model, CRUD APIs)
2. **002-ui-layout-dashboard** is complete (Sidebar, i18n infrastructure)
3. Development environment is running:

   ```bash
   # Terminal 1: Backend
   cd backend && uvicorn src.main:app --reload --port 8000

   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

## Implementation Order

### Phase 1: Backend Foundation

1. **Database Migration** - Add sort_order to accounts, create audit_logs table

   ```bash
   cd backend
   alembic revision --autogenerate -m "Add sort_order and audit_logs"
   alembic upgrade head
   ```

2. **Audit Service** - Create `backend/src/services/audit_service.py`
   - `log_create(entity_type, entity_id, new_value, ledger_id)`
   - `log_update(entity_type, entity_id, old_value, new_value, ledger_id)`
   - `log_delete(entity_type, entity_id, old_value, ledger_id)`
   - `log_reassign(from_account_id, to_account_id, transaction_count, ledger_id)`

3. **Account Service Extensions** - Extend `backend/src/services/account_service.py`
   - `reorder_accounts(ledger_id, parent_id, account_ids)` - Update sort_order
   - `can_delete(ledger_id, account_id)` - Return deletion status
   - `reassign_transactions(ledger_id, from_id, to_id)` - Bulk UPDATE
   - `get_replacement_candidates(ledger_id, account_id)` - Filter same type

4. **API Routes** - Extend `backend/src/api/routes/accounts.py`
   - `PATCH /ledgers/{id}/accounts/reorder`
   - `GET /ledgers/{id}/accounts/{id}/can-delete`
   - `GET /ledgers/{id}/accounts/{id}/replacement-candidates`
   - `POST /ledgers/{id}/accounts/{id}/reassign`

### Phase 2: Frontend Settings Infrastructure

5. **User Preferences Hook** - Create `frontend/src/lib/hooks/useUserPreferences.ts`

   ```typescript
   interface UserPreferences {
     language: "zh-TW" | "en";
     theme: "light" | "dark" | "system";
   }

   export function useUserPreferences() {
     // Read/write localStorage with SSR safety
   }
   ```

6. **Theme Context** - Create `frontend/src/lib/context/ThemeContext.tsx`

   ```bash
   npm install next-themes
   ```

   - Wrap app with ThemeProvider
   - Integrate with useUserPreferences

7. **Settings Page Structure** - Create routes

   ```
   frontend/src/app/settings/
   ├── page.tsx          # Main settings with language/theme
   └── accounts/
       └── page.tsx      # Account management
   ```

8. **Sidebar Update** - Add Settings link to `Sidebar.tsx`

### Phase 3: Account Management UI

9. **Drag-and-Drop Setup**

   ```bash
   cd frontend
   npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
   ```

10. **AccountTree Component** - Create `frontend/src/components/accounts/AccountTree.tsx`
    - Render hierarchical tree with drag handles
    - Support reordering within parent
    - Support reparenting (drag onto another account)
    - Call reorder API on drop

11. **Account Form Dialog** - Extend for create/edit
    - Name input with validation
    - Type selector (create only)
    - Parent selector with depth validation

12. **Delete Account Dialog** - Create `DeleteAccountDialog.tsx`
    - Check can-delete first
    - Show transaction count if blocked
    - Replacement account selector
    - Confirm reassignment and delete

### Phase 4: i18n Extensions

13. **Message Files** - Add to `frontend/messages/en.json` and `zh-TW.json`:
    ```json
    {
      "settings": {
        "title": "Settings",
        "accounts": "Account Management",
        "language": "Language",
        "theme": "Theme",
        "themeLight": "Light",
        "themeDark": "Dark",
        "themeSystem": "System"
      },
      "accountManagement": {
        "addAccount": "Add Account",
        "editAccount": "Edit Account",
        "deleteAccount": "Delete Account",
        "confirmDelete": "Are you sure?",
        "hasTransactions": "This account has {count} transactions",
        "selectReplacement": "Select replacement account",
        "reassignAndDelete": "Reassign & Delete",
        "cannotDeleteChildren": "Remove child accounts first",
        "maxDepthReached": "Maximum nesting level reached"
      }
    }
    ```

## Key Files Reference

| Component            | Location                                                 |
| -------------------- | -------------------------------------------------------- |
| Account Model        | `backend/src/models/account.py`                          |
| Account Service      | `backend/src/services/account_service.py`                |
| Audit Service        | `backend/src/services/audit_service.py` (NEW)            |
| Account Routes       | `backend/src/api/routes/accounts.py`                     |
| Settings Page        | `frontend/src/app/settings/page.tsx` (NEW)               |
| Account Management   | `frontend/src/app/settings/accounts/page.tsx` (NEW)      |
| AccountTree          | `frontend/src/components/accounts/AccountTree.tsx` (NEW) |
| UserPreferences Hook | `frontend/src/lib/hooks/useUserPreferences.ts` (NEW)     |
| Theme Context        | `frontend/src/lib/context/ThemeContext.tsx` (NEW)        |
| Sidebar              | `frontend/src/components/layout/Sidebar.tsx`             |

## Testing Checkpoints

After each phase, verify:

### Backend Tests

```bash
cd backend
pytest tests/unit/test_account_service.py -v
pytest tests/unit/test_audit_service.py -v
pytest tests/integration/test_account_reassign.py -v
pytest tests/contract/test_account_api.py -v
```

### Frontend Tests

```bash
cd frontend
npm run test -- --run tests/hooks/useUserPreferences.test.ts
npm run test -- --run tests/components/settings/
```

### Manual Verification

1. Settings accessible from sidebar
2. Can create account at each depth level
3. Cannot create account at depth 4
4. Drag reorder persists after refresh
5. Delete account with transactions shows replacement dialog
6. Language switch immediate, persists after refresh
7. Theme switch immediate, persists after refresh
8. Mobile: touch-hold initiates drag

## Common Pitfalls

1. **Sort order gaps**: Use multiples of 1000 to allow insertions without reordering all
2. **Circular ref check**: Must check BEFORE saving, not after
3. **Theme flash**: Ensure next-themes suppressHydrationWarning is set
4. **i18n hydration**: Use `useTranslations()` in client components only
5. **Drag on mobile**: Ensure touch-action CSS allows drag gestures
