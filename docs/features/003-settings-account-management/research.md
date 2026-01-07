# Research: Settings & Account Management

**Feature**: 003-settings-account-management
**Date**: 2026-01-07
**Phase**: 0 - Research & Unknowns Resolution

## Research Tasks

### 1. Drag-and-Drop Library for React

**Context**: FR-011 requires drag-and-drop reordering of accounts in a tree structure.

**Decision**: @dnd-kit/core + @dnd-kit/sortable

**Rationale**:
- Modern, accessible, and performant drag-and-drop library for React
- Native support for tree structures via @dnd-kit/sortable
- Works well with Next.js and React 19
- Excellent TypeScript support
- Smaller bundle size than alternatives (react-beautiful-dnd deprecated)
- Supports touch devices for mobile drag-and-drop (FR meets SC-007)

**Alternatives Considered**:
- react-beautiful-dnd: Deprecated, no longer maintained by Atlassian
- react-dnd: Lower-level, more complex setup for tree structures
- Native HTML5 drag-and-drop: Limited styling, poor mobile support

### 2. Theme Switching Implementation

**Context**: FR-017/FR-019 require dark/light mode toggle with system default detection.

**Decision**: Tailwind CSS dark mode with `class` strategy + next-themes

**Rationale**:
- Tailwind's `dark:` variant already available in the project
- next-themes provides SSR-safe theme detection and switching
- Integrates with system preference detection (`prefers-color-scheme`)
- localStorage persistence built-in (aligns with clarification: browser local storage only)
- No flash of unstyled content (FOUC) prevention

**Alternatives Considered**:
- CSS custom properties only: Would require manual system detection
- React context only: SSR hydration issues with Next.js
- Tailwind `media` strategy: Can't override system preference

### 3. Account Audit Trail Implementation

**Context**: DI-004 requires audit trail for account CRUD operations.

**Decision**: Dedicated AuditLog table with polymorphic entity references

**Rationale**:
- Separate table keeps Account model clean
- Polymorphic design allows future expansion to other entity types
- Stores: entity_type, entity_id, action, old_value (JSON), new_value (JSON), timestamp, user_context
- Follows existing timestamp patterns in the codebase

**Alternatives Considered**:
- Database triggers: Less portable, harder to include application context
- Event sourcing: Over-engineering for current scope
- Soft deletes with history columns: Clutters the Account table

### 4. Transaction Reassignment Strategy

**Context**: FR-009 requires reassigning transactions when deleting an account with transactions.

**Decision**: Bulk UPDATE operation with transactional integrity

**Rationale**:
- Single database transaction for atomicity
- UPDATE transactions SET account_id = :replacement_id WHERE account_id = :deleted_id
- Validates replacement account exists and is same type before proceeding
- Audit log captures the reassignment action with both account IDs

**Alternatives Considered**:
- Row-by-row update: Slower, higher transaction overhead
- Soft delete account instead: Doesn't match user expectation of deletion

### 5. Account Sort Order Persistence

**Context**: FR-012 requires persisting custom account order.

**Decision**: Add `sort_order` integer field to Account model

**Rationale**:
- Simple integer ordering, reordering updates affected accounts only
- Uses gap strategy (sort_order = position * 1000) to minimize reordering cascades
- Backend reorder endpoint accepts array of account IDs in desired order
- Sidebar queries already support ORDER BY, just need to include sort_order

**Alternatives Considered**:
- Linked list (next_sibling_id): Complex queries for retrieving ordered list
- String-based ordering (lexicographic): Requires complex maintenance
- Separate ordering table: Unnecessary indirection

### 6. Settings Page Navigation Structure

**Context**: FR-001/FR-002 require Settings entry point with Account Management section.

**Decision**: Nested route structure: `/settings` with sub-routes

**Rationale**:
- `/settings` - Main settings page with navigation to subsections
- `/settings/accounts` - Account management page
- `/settings/preferences` - Language/theme settings (can be inline on main settings page)
- Follows Next.js app router conventions
- Sidebar adds single "Settings" link, internal navigation within settings pages

**Alternatives Considered**:
- Modal-based settings: Limited space for account tree
- Sidebar expansion for settings: Clutters navigation
- Single monolithic settings page: Poor UX for account management complexity

### 7. Hierarchy Depth Validation

**Context**: FR-013/FR-014 require 3-level max hierarchy with prevention of deeper nesting.

**Decision**: Calculate depth from parent chain, validate on create/move

**Rationale**:
- Existing Account model has `depth` field (1-3)
- On create: If parent.depth >= 3, reject with error
- On drag-drop move: Validate new_parent.depth < 3 before allowing reparent
- Frontend disables drop targets for depth-3 accounts

**Alternatives Considered**:
- Database constraint: Can't easily express tree depth constraint
- Recursive CTE check: Overhead for every operation, existing depth field sufficient

### 8. Circular Reference Prevention

**Context**: DI-003 requires preventing circular parent-child relationships.

**Decision**: Ancestor check before save

**Rationale**:
- When setting parent_id, traverse up parent chain
- If proposed parent is found in account's descendants, reject
- Backend validation ensures integrity even if frontend bypassed
- Simple recursive query: Check if new_parent_id appears in account's subtree

**Alternatives Considered**:
- Database trigger: Less portable
- Path materialization (ltree): Overkill for 3-level max depth

### 9. Unique Name Validation Scope

**Context**: FR-005 requires unique account names within same parent.

**Decision**: Composite uniqueness constraint (ledger_id, parent_id, name)

**Rationale**:
- Allows same name in different ledgers
- Allows same name under different parents (e.g., "Checking" under multiple banks)
- Database constraint ensures integrity
- Friendly error message on duplicate attempt

**Alternatives Considered**:
- Global uniqueness per ledger: Too restrictive
- No constraint (allow duplicates): Confusing for users

### 10. i18n Integration for Settings

**Context**: FR-015 requires language switching; existing next-intl infrastructure.

**Decision**: Extend existing message files with `settings` namespace

**Rationale**:
- Add `settings: { ... }` key to en.json and zh-TW.json
- Language selector reads/writes locale from next-intl's locale state
- Persist to localStorage via useUserPreferences hook
- On app load, check localStorage for preference before defaulting

**Alternatives Considered**:
- Separate settings i18n file: Unnecessary complexity
- URL-based locale (existing): Works, but need persistence layer

## Dependencies Summary

### New npm packages (Frontend)
- `@dnd-kit/core`: ^6.1.0
- `@dnd-kit/sortable`: ^8.0.0
- `@dnd-kit/utilities`: ^3.2.0
- `next-themes`: ^0.4.0

### Database Changes
- Account table: Add `sort_order` INTEGER DEFAULT 0
- New AuditLog table: id, entity_type, entity_id, action, old_value, new_value, timestamp

### API Additions
- PATCH `/ledgers/{ledger_id}/accounts/reorder` - Reorder accounts
- POST `/ledgers/{ledger_id}/accounts/{account_id}/reassign` - Reassign transactions
- GET `/audit-logs` - Query audit logs (future, admin use)

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Drag-drop performance with large account trees | Tree virtualization if >100 accounts; gap-based sort_order minimizes DB writes |
| Theme flash on page load | next-themes handles SSR/hydration safely |
| Concurrent account edits | Last-write-wins acceptable for single-user app; updated_at prevents lost updates |
| Mobile drag-drop usability | dnd-kit touch support + touch-hold gesture; test on real devices |
