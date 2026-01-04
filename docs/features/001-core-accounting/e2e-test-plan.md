# E2E Test Plan: Core Accounting System

## Overview

This document outlines the End-to-End (E2E) test strategy for the Core Accounting System feature, covering user flows from the frontend through the backend API to the database.

## Scope

### In Scope
- User setup and authentication flow
- Ledger CRUD operations
- Account CRUD operations (including hierarchical accounts)
- Transaction CRUD operations
- Account tree rendering and navigation
- Balance calculations and aggregation
- Filter and search functionality

### Out of Scope
- Unit tests (covered separately)
- Performance/load testing
- Security penetration testing
- Accessibility testing (separate plan)

## Test Environment

### Prerequisites
- PostgreSQL database (Docker or Supabase)
- Backend API server running on `localhost:8000`
- Frontend Next.js server running on `localhost:3000`
- Clean database state before each test suite

### Test Data Strategy
- Each test suite should create its own test data
- Use unique identifiers (timestamps/UUIDs) to avoid conflicts
- Clean up test data after suite completion when possible

## Test Categories

### 1. User Setup Flow
- Initial user registration/setup
- User session persistence
- Multi-user isolation

### 2. Ledger Management
- Create ledger with initial balance
- View ledger list
- View single ledger details
- Update ledger name
- Delete ledger (cascade behavior)
- Ledger isolation between users

### 3. Account Management
- Create root-level accounts (all types: ASSET, LIABILITY, INCOME, EXPENSE)
- Create child accounts (level 2)
- Create grandchild accounts (level 3, max depth)
- Attempt to create beyond max depth (expect failure)
- View account list (flat)
- View account tree (hierarchical)
- Expand/collapse account tree in UI
- Update account name
- Delete leaf accounts
- Attempt to delete accounts with children (expect failure)
- Attempt to delete accounts with transactions (expect failure)
- Delete system accounts (expect failure)
- Type consistency validation (child must match parent type)

### 4. Transaction Management
- Create EXPENSE transaction (Asset/Liability → Expense)
- Create INCOME transaction (Income → Asset/Liability)
- Create TRANSFER transaction (Asset/Liability → Asset/Liability)
- Invalid transaction type combinations (expect failures)
- Transaction on leaf accounts only
- Attempt transaction on parent accounts (expect failure)
- Update transaction
- Delete transaction
- Transaction list with pagination
- Transaction search by description
- Transaction filter by date range
- Transaction filter by account
- Transaction filter by type

### 5. Balance Calculations
- Verify account balance after transactions
- Verify parent account aggregates child balances
- Verify balance updates after transaction edit
- Verify balance updates after transaction delete
- Negative balance warning display

### 6. Cross-Feature Flows
- Complete user journey: setup → create ledger → create accounts → record transactions
- Ledger deletion cascades to accounts and transactions
- Account hierarchy with transactions flow

## Test Execution

### Priority Levels
- **P0 (Critical)**: Must pass for release - core CRUD operations
- **P1 (High)**: Important functionality - hierarchy, balance calculations
- **P2 (Medium)**: Enhanced features - filters, search, pagination
- **P3 (Low)**: Edge cases and error handling

### Automation Strategy
- Use Playwright for browser automation
- API tests using pytest with httpx
- Run on CI/CD pipeline for every PR
- Nightly full regression suite

## Success Criteria

- All P0 tests pass: 100%
- All P1 tests pass: 100%
- P2 tests pass: >= 95%
- P3 tests pass: >= 90%
- No critical or high severity bugs in production paths

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database state pollution | High | Isolated test databases per suite |
| Flaky tests | Medium | Proper waits, retry mechanisms |
| Test data dependencies | Medium | Self-contained test suites |
| API changes breaking tests | Medium | Centralized API client helpers |

## Schedule

| Phase | Duration | Activities |
|-------|----------|------------|
| Setup | 1 day | Environment setup, framework configuration |
| P0 Tests | 2 days | Critical path test implementation |
| P1 Tests | 2 days | Hierarchy and balance tests |
| P2/P3 Tests | 2 days | Filters, search, edge cases |
| Review | 1 day | Test review and documentation |
