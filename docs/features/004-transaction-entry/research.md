# Research: Transaction Entry

**Feature**: 004-transaction-entry
**Date**: 2026-01-09
**Purpose**: Resolve technical unknowns and document design decisions

## 1. Expression Parser for Amount Input

### Decision

Use a simple recursive descent parser for basic arithmetic expressions (+, -, \*, /) with proper operator precedence.

### Rationale

- Simple expressions only (no parentheses, no functions) keeps implementation straightforward
- Frontend-only calculation provides instant feedback
- Backend validation ensures final amount is correct (doesn't need to parse expression)

### Alternatives Considered

| Alternative           | Pros                    | Cons                               | Rejected Because                 |
| --------------------- | ----------------------- | ---------------------------------- | -------------------------------- |
| math.js library       | Full expression support | 50KB+ bundle size, overkill        | Too heavy for simple use case    |
| Direct code execution | Zero implementation     | Critical security vulnerability    | Never execute user input as code |
| Backend calculation   | Consistent precision    | Network latency for each keystroke | Poor UX                          |

### Implementation Notes

```typescript
// Expression grammar:
// expr    = term (('+' | '-') term)*
// term    = factor (('*' | '/') factor)*
// factor  = NUMBER

// Example: "50+40*2" → 50 + (40*2) = 130
// Safe parsing - no code execution, just tokenizing and arithmetic
```

## 2. Modal Dialog vs Other UI Patterns

### Decision

Use Modal Dialog for transaction entry form.

### Rationale

- Consistent with existing patterns in 003-settings-account-management (AccountForm uses dialog)
- Focuses user attention on single task
- Easy to implement with existing ShadcnUI Dialog component
- Mobile-friendly with full-screen takeover on small screens

### Alternatives Considered

| Alternative      | Pros        | Cons                             | Rejected Because              |
| ---------------- | ----------- | -------------------------------- | ----------------------------- |
| Slide-over panel | Modern feel | Less mobile-friendly             | Inconsistent with existing UX |
| Inline expansion | No overlay  | Disrupts transaction list layout | Layout complexity             |
| New page         | Full space  | Navigation overhead              | Disrupts user flow            |

## 3. Date Picker Component

### Decision

Use ShadcnUI's date picker component with react-day-picker.

### Rationale

- Already included in ShadcnUI component library
- Accessible and keyboard-navigable
- Supports localization (zh-TW, en)
- "Today" quick-select is built-in

### Implementation Notes

- Default to today's date on form open
- Store dates in ISO format (YYYY-MM-DD)
- Display in locale-appropriate format

## 4. Template Storage Strategy

### Decision

Store templates in a separate `transaction_templates` table with foreign keys to accounts.

### Rationale

- Clean separation from transactions
- Allows independent template management
- Foreign keys ensure referential integrity
- sort_order field enables drag-drop reordering

### Alternatives Considered

| Alternative          | Pros              | Cons                   | Rejected Because    |
| -------------------- | ----------------- | ---------------------- | ------------------- |
| JSON field in ledger | Simple schema     | Hard to query/validate | Poor data integrity |
| localStorage only    | No backend needed | Lost on device change  | Data loss risk      |

## 5. Quick Entry Location

### Decision

Dashboard quick-entry panel showing template buttons.

### Rationale

- Dashboard is the natural landing page
- Quick entry is for rapid, repeated actions
- Keeps account pages focused on transaction history
- Can show recent/favorite templates prominently

### Implementation Notes

- Panel shows up to 8 most-used templates
- "See all" link opens full template list
- Confirmation dialog before saving (per FR-027)

## 6. Account Selection Dropdown

### Decision

Use hierarchical dropdown matching sidebar account tree structure.

### Rationale

- Consistent with 003-settings-account-management AccountTree
- Users are already familiar with the hierarchy
- Grouped by account type (Asset, Liability, Income, Expense)

### Implementation Notes

- Pre-select current account as From (for Asset/Expense) or To (for Income/Liability)
- Auto-suggest transaction type based on From account type
- Filter out same account from opposite dropdown

## 7. Notes Field Storage

### Decision

Add optional `notes` field to existing Transaction model (VARCHAR 500).

### Rationale

- Extends existing model minimally
- 500 characters sufficient for detailed notes
- Optional field doesn't affect existing transactions

### Migration Strategy

- Alembic migration to add nullable `notes` column
- No data migration needed (existing transactions have NULL notes)

## 8. Expression Storage (Audit Trail)

### Decision

Store original expression in a separate `amount_expression` field when used.

### Rationale

- DI-005 requires calculation traceability
- Useful for audit: "user entered 50+40+10, result was 100"
- Optional field (NULL when direct number entered)

### Implementation Notes

- Frontend sends both `amount` (calculated) and `amount_expression` (original)
- Backend validates `amount` matches expression result
- Display expression in transaction detail view if present

## Dependencies Summary

| Dependency             | Version | Purpose                                            |
| ---------------------- | ------- | -------------------------------------------------- |
| @radix-ui/react-dialog | ^1.0.0  | Modal dialog (via ShadcnUI)                        |
| react-day-picker       | ^8.10.0 | Date picker (via ShadcnUI)                         |
| date-fns               | ^3.2.0  | Date formatting (already installed)                |
| zod                    | ^3.22.0 | Form validation (already installed)                |
| @dnd-kit/core          | ^6.3.1  | Drag-drop for template reorder (already installed) |

## Open Questions (Resolved)

All technical unknowns have been resolved. Ready to proceed to Phase 1 (Design & Contracts).
