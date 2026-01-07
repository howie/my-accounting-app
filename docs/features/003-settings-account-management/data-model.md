# Data Model: Settings & Account Management

**Feature**: 003-settings-account-management
**Date**: 2026-01-07
**Phase**: 1 - Design & Contracts

## Entity Overview

This feature extends the existing Account entity and introduces a new AuditLog entity. User preferences are stored in browser localStorage (not database).

## Entity Definitions

### Account (Extended)

Extends existing Account model from 001-core-accounting.

```
Account
├── id: UUID (PK) [existing]
├── ledger_id: UUID (FK → Ledger.id) [existing]
├── name: String(100) [existing, validated 1-100 chars]
├── type: Enum(ASSET, LIABILITY, INCOME, EXPENSE) [existing]
├── parent_id: UUID (FK → Account.id, nullable) [existing]
├── depth: Integer (1-3) [existing]
├── is_system: Boolean [existing]
├── balance: Decimal [existing]
├── sort_order: Integer [NEW, default 0]
├── created_at: DateTime [existing]
└── updated_at: DateTime [existing]
```

**New Field Details**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | Custom ordering within parent; lower values appear first |

**Validation Rules**:
- name: Required, 1-100 characters, unique within (ledger_id, parent_id)
- parent_id: Must reference valid Account in same ledger
- depth: Auto-calculated as parent.depth + 1; max 3
- sort_order: Non-negative integer; gap strategy (multiples of 1000)

**Business Rules**:
- Cannot delete account with child accounts (must delete/move children first)
- Cannot delete account with transactions (must reassign transactions first)
- Cannot set parent_id to create cycle (ancestor check required)
- Cannot set parent_id if it would result in depth > 3

### AuditLog (New)

Tracks changes to entities for audit trail compliance (DI-004).

```
AuditLog
├── id: UUID (PK)
├── entity_type: String(50)
├── entity_id: UUID
├── action: Enum(CREATE, UPDATE, DELETE, REASSIGN)
├── old_value: JSON (nullable)
├── new_value: JSON (nullable)
├── metadata: JSON (nullable)
├── timestamp: DateTime
└── ledger_id: UUID (FK → Ledger.id)
```

**Field Details**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| entity_type | VARCHAR(50) | NOT NULL | Type of entity (e.g., "Account") |
| entity_id | UUID | NOT NULL | ID of the affected entity |
| action | VARCHAR(20) | NOT NULL | Type of action performed |
| old_value | JSONB | NULLABLE | Previous state (for UPDATE/DELETE) |
| new_value | JSONB | NULLABLE | New state (for CREATE/UPDATE) |
| metadata | JSONB | NULLABLE | Additional context (e.g., reassigned_to_id) |
| timestamp | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When the action occurred |
| ledger_id | UUID | FK, NOT NULL | Ledger context for filtering |

**Indexes**:
- `idx_audit_entity`: (entity_type, entity_id) - Query logs for specific entity
- `idx_audit_timestamp`: (ledger_id, timestamp DESC) - Query recent logs
- `idx_audit_action`: (ledger_id, action) - Query by action type

### UserPreferences (Frontend Only)

Stored in browser localStorage, not database.

```
UserPreferences (localStorage)
├── language: "zh-TW" | "en"
├── theme: "light" | "dark" | "system"
└── sidebarState: { [categoryId]: boolean }  [existing]
```

**Storage Key**: `myab_user_preferences`

**Schema**:
```typescript
interface UserPreferences {
  language: 'zh-TW' | 'en';
  theme: 'light' | 'dark' | 'system';
}
```

**Default Values**:
- language: Browser's navigator.language or 'zh-TW'
- theme: 'system' (respects OS preference)

## Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                         Ledger                               │
│  ├── has many → Account (one-to-many)                       │
│  └── has many → AuditLog (one-to-many, for filtering)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         Account                              │
│  ├── belongs to → Ledger (many-to-one)                      │
│  ├── belongs to → Account (self-ref, parent)                │
│  ├── has many → Account (self-ref, children)                │
│  └── has many → Transaction (via from_account, to_account)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        AuditLog                              │
│  ├── references → Any entity (polymorphic via entity_type)  │
│  └── belongs to → Ledger (for scoping queries)              │
└─────────────────────────────────────────────────────────────┘
```

## State Transitions

### Account Lifecycle

```
                    ┌──────────────┐
                    │   Created    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │ Renamed │  │ Moved   │  │Reordered│
        └────┬────┘  └────┬────┘  └────┬────┘
              │            │            │
              └────────────┼────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │ Delete  │  │ Delete  │  │ Delete  │
        │(no txn) │  │ (txns)  │  │(w/child)│
        └────┬────┘  └────┬────┘  └────┬────┘
              │            │            │
              │       ┌────┴────┐       │
              │       ▼         │       │
              │  ┌─────────┐    │  ┌────┴────┐
              │  │Reassign │    │  │ BLOCKED │
              │  │  Txns   │    │  └─────────┘
              │  └────┬────┘    │
              │       │         │
              ▼       ▼         ▼
        ┌─────────────────────────┐
        │        Deleted          │
        └─────────────────────────┘
```

### Audit Actions

| Action | Trigger | old_value | new_value | metadata |
|--------|---------|-----------|-----------|----------|
| CREATE | Account created | null | Full account JSON | null |
| UPDATE | Name changed | { name: old } | { name: new } | null |
| UPDATE | Parent changed | { parent_id: old } | { parent_id: new } | null |
| UPDATE | Reordered | { sort_order: old } | { sort_order: new } | null |
| REASSIGN | Txns moved | null | null | { from_account_id, to_account_id, transaction_count } |
| DELETE | Account deleted | Full account JSON | null | null |

## Database Migration

### Migration: Add sort_order to Account

```sql
-- Up
ALTER TABLE accounts ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0;

-- Initialize sort_order based on current name ordering
WITH ordered AS (
  SELECT id, ROW_NUMBER() OVER (
    PARTITION BY ledger_id, parent_id
    ORDER BY name
  ) * 1000 AS new_order
  FROM accounts
)
UPDATE accounts SET sort_order = ordered.new_order
FROM ordered WHERE accounts.id = ordered.id;

-- Down
ALTER TABLE accounts DROP COLUMN sort_order;
```

### Migration: Create AuditLog table

```sql
-- Up
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type VARCHAR(50) NOT NULL,
  entity_id UUID NOT NULL,
  action VARCHAR(20) NOT NULL,
  old_value JSONB,
  new_value JSONB,
  metadata JSONB,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ledger_id UUID NOT NULL REFERENCES ledgers(id) ON DELETE CASCADE
);

CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(ledger_id, timestamp DESC);
CREATE INDEX idx_audit_action ON audit_logs(ledger_id, action);

-- Down
DROP TABLE audit_logs;
```

## Constraints Summary

| Constraint | Table | Type | Definition |
|------------|-------|------|------------|
| uk_account_name | accounts | UNIQUE | (ledger_id, parent_id, name) |
| chk_account_depth | accounts | CHECK | depth BETWEEN 1 AND 3 |
| chk_sort_order | accounts | CHECK | sort_order >= 0 |
| fk_audit_ledger | audit_logs | FK | ledger_id → ledgers(id) |

## Query Patterns

### Get ordered account tree

```sql
SELECT * FROM accounts
WHERE ledger_id = :ledger_id
ORDER BY
  CASE type
    WHEN 'ASSET' THEN 1
    WHEN 'LIABILITY' THEN 2
    WHEN 'INCOME' THEN 3
    WHEN 'EXPENSE' THEN 4
  END,
  depth,
  sort_order,
  name;
```

### Check for circular reference

```sql
WITH RECURSIVE ancestors AS (
  SELECT id, parent_id FROM accounts WHERE id = :new_parent_id
  UNION ALL
  SELECT a.id, a.parent_id FROM accounts a
  JOIN ancestors anc ON a.id = anc.parent_id
)
SELECT EXISTS (SELECT 1 FROM ancestors WHERE id = :account_id);
```

### Get replacement account candidates

```sql
SELECT id, name, depth FROM accounts
WHERE ledger_id = :ledger_id
  AND type = :account_type
  AND id != :account_id
  AND depth < 3  -- Can still accept children
ORDER BY sort_order, name;
```
