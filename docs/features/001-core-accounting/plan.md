# Implementation Plan: Core Accounting System

**Branch**: `001-core-accounting` | **Date**: 2025-11-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/001-core-accounting/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Building a core double-entry accounting system that enables users to track personal finances through ledgers, accounts, and transactions. The system enforces strict data integrity through double-entry bookkeeping, supports multiple ledgers per user, and provides transaction search/filtering capabilities. This is the foundational feature that all other accounting features will depend on.

**Technical Approach**: Python desktop application using SQLite for local data storage, following TDD principles with comprehensive test coverage for financial calculations and data integrity.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: SQLite (built-in), pytest (testing), tkinter (GUI - bundled with Python)
**Storage**: SQLite database (single file per user account, up to 30,000 transactions per ledger)
**Testing**: pytest for unit/integration tests, pytest-cov for coverage
**Target Platform**: Desktop (Windows, macOS initially; Linux compatibility)
**Project Type**: Single desktop application (not web/mobile at this stage)
**Performance Goals**:
- Transaction entry: < 100ms response
- Balance calculations: < 100ms for typical use (< 10k transactions)
- Search/filter: < 500ms for up to 5,000 transactions
- Database operations: < 10ms for single transaction CRUD

**Constraints**:
- 30,000 transaction limit per ledger (SQLite optimization boundary)
- Single-user desktop mode (no concurrent editing)
- Offline-first (no network required for core functionality)
- Password alphanumeric only (security constraint from spec)
- 125 character description display limit

**Scale/Scope**:
- Target: Personal finance users (1-5 ledgers per user typical)
- Expected transactions: 100-500 per month per active ledger
- User accounts: 1-10 per installation (family members)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with all five core principles from `.specify/memory/constitution.md`:

### I. Data-First Design (NON-NEGOTIABLE)
- [x] Does this feature preserve financial accuracy (calculations correct to the cent)?
  - Yes: All amounts stored as DECIMAL(19,2) or Python Decimal type
- [x] Are audit trails maintained (all modifications logged with timestamp/reason)?
  - Yes: Transaction table includes created_at, modified_at timestamps; all modifications create new transaction records
- [x] Is data loss prevented (confirmations + backups for destructive operations)?
  - Yes: Delete operations require confirmation (FR-008, DI-004); ledger deletion shows warning
- [x] Is input validation enforced (amounts, dates, account references)?
  - Yes: DI-001 mandates numeric validation; FR-006 validates transaction rules; foreign key constraints enforce account references
- [x] Are destructive operations reversible?
  - Yes: Through backup/restore (out of scope for this feature, but data structure supports); no undo within app per C-005

**Violations**: None

### II. Test-First Development (NON-NEGOTIABLE)
- [x] Will tests be written BEFORE implementation?
  - Yes: TDD workflow required; tests for each user story before implementation
- [x] Will tests be reviewed/approved before coding?
  - Yes: Test review checkpoint in tasks.md workflow
- [x] Are contract tests planned for service boundaries?
  - Yes: Service layer (UserAccountService, LedgerService, TransactionService) will have contract tests
- [x] Are integration tests planned for multi-account transactions?
  - Yes: User Story 2 scenarios explicitly test double-entry balance updates across accounts
- [x] Are edge case tests planned (rounding, currency, date boundaries)?
  - Yes: Edge cases section lists 7 scenarios including zero amounts, large amounts, future dates, overdrafts

**Violations**: None

### III. Financial Accuracy & Audit Trail
- [x] Does design maintain double-entry bookkeeping (debits = credits)?
  - Yes: FR-002, DI-003 enforce this; every transaction has debit_account and credit_account with equal amounts
- [x] Are transactions immutable once posted (void-and-reenter only)?
  - No: FR-007 allows editing existing transactions. **JUSTIFIED**: Spec assumption A-006 explicitly states users accept immediate balance updates; no audit lock for closed periods required for personal finance use case
- [x] Are calculations traceable to source transactions?
  - Yes: DI-005 requires this; balance = SUM of all transactions for account
- [x] Are timestamps tracked (created, modified, business date)?
  - Yes: transaction_date (business date), created_at, modified_at all tracked
- [x] Is change logging implemented (who, what, when, why)?
  - Partial: Who/what/when through timestamps; "why" not required for personal finance (single user, no compliance needs)

**Violations**: Transaction mutability justified by personal finance use case (Assumption A-006)

### IV. Simplicity & Maintainability
- [x] Is this feature actually needed (not speculative)?
  - Yes: Core accounting is foundational; no features without it
- [x] Is the design clear over clever (human-auditable)?
  - Yes: Direct SQL queries, simple Python classes for models, no ORM magic
- [x] Are abstractions minimized (especially for financial calculations)?
  - Yes: Balance calculation is SUM query; transaction validation is explicit if/else; no framework abstractions
- [x] Are complex business rules documented with accounting references?
  - Yes: Double-entry bookkeeping explicitly documented; account types follow standard accounting classification (Asset/Liability/Income/Expense)

**Violations**: None

### V. Cross-Platform Consistency
- [x] Will calculations produce identical results across platforms?
  - Yes: Python Decimal + SQLite produce consistent results on Windows/macOS/Linux
- [x] Is data format compatible between desktop and web?
  - N/A for this feature: Desktop only (A-005); web/mobile out of scope
- [x] Are platform-specific features clearly documented?
  - Yes: Desktop-only noted in assumptions; GUI using tkinter (cross-platform)
- [x] Do workflows follow consistent UX patterns?
  - Yes: Standard desktop patterns (double-click to edit, delete key, search bar)
- [x] Does cloud sync maintain transaction ordering?
  - N/A for this feature: Cloud sync out of scope (handled by external providers per A-003)

**Violations**: None (cross-platform considerations addressed within desktop scope)

**Overall Assessment**: **PASS**

All five constitution principles are satisfied. The one justifiable deviation (transaction mutability vs. immutability) is explicitly documented in the spec assumptions and appropriate for personal finance software.

## Project Structure

### Documentation (this feature)

```text
docs/features/001-core-accounting/
├── spec.md              # Feature specification ✓
├── plan.md              # This file (implementation plan) ✓
├── research.md          # Phase 0: Technology decisions
├── data-model.md        # Phase 1: Database schema
├── quickstart.md        # Phase 1: Developer guide
├── contracts/           # Phase 1: Service contracts
│   ├── user_account_service.md
│   ├── ledger_service.md
│   ├── account_service.md
│   └── transaction_service.md
├── tasks.md             # Phase 2: Task breakdown (generated by /speckit.tasks)
├── checklists/          # Quality validation ✓
│   └── requirements.md
└── issues/              # Issue tracking ✓
```

### Source Code (repository root)

```text
src/
├── myab/                      # Main application package
│   ├── __init__.py
│   ├── models/                # Data models
│   │   ├── __init__.py
│   │   ├── user_account.py    # UserAccount model
│   │   ├── ledger.py          # Ledger model
│   │   ├── account.py         # Account (category) model
│   │   └── transaction.py     # Transaction model
│   ├── services/              # Business logic layer
│   │   ├── __init__.py
│   │   ├── user_account_service.py
│   │   ├── ledger_service.py
│   │   ├── account_service.py
│   │   └── transaction_service.py
│   ├── persistence/           # Database layer
│   │   ├── __init__.py
│   │   ├── database.py        # SQLite connection manager
│   │   └── repositories/      # Data access objects
│   │       ├── __init__.py
│   │       ├── user_account_repository.py
│   │       ├── ledger_repository.py
│   │       ├── account_repository.py
│   │       └── transaction_repository.py
│   ├── ui/                    # GUI layer (tkinter)
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── ledger_management.py
│   │   ├── account_management.py
│   │   └── transaction_entry.py
│   └── validation/            # Input validation
│       ├── __init__.py
│       └── validators.py
│
tests/
├── contract/                  # Service contract tests
│   ├── __init__.py
│   ├── test_user_account_service_contract.py
│   ├── test_ledger_service_contract.py
│   ├── test_account_service_contract.py
│   └── test_transaction_service_contract.py
├── integration/               # Integration tests
│   ├── __init__.py
│   ├── test_ledger_lifecycle.py
│   ├── test_transaction_flow.py
│   └── test_balance_calculations.py
├── unit/                      # Unit tests
│   ├── models/
│   ├── services/
│   ├── persistence/
│   └── validation/
└── fixtures/                  # Test data
    ├── __init__.py
    └── sample_data.py

.venv/                         # Python virtual environment (gitignored)
requirements.txt               # Production dependencies
requirements-dev.txt           # Development dependencies (pytest, etc.)
setup.py or pyproject.toml     # Package configuration
README.md                      # Project readme
```

**Structure Decision**: Single desktop application structure selected.

**Rationale**:
- Desktop-only scope (Assumption A-005) rules out web/mobile structure
- No backend API needed (offline-first, local SQLite)
- Standard Python package layout with clear separation:
  - `models/`: Pure data classes (POPOs - Plain Old Python Objects)
  - `services/`: Business logic implementing accounting rules
  - `persistence/`: Database access isolated to repositories
  - `ui/`: GUI code separate from business logic for testability
  - `validation/`: Reusable validators for DI-001 compliance

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Transaction mutability (Principle III) | Personal finance users need to correct mistakes without void-and-reenter workflow | Immutable transactions would require complex void/correction UI unsuitable for non-accountant users |

## Phase 0: Research & Technology Decisions

**Status**: ✅ COMPLETE

All technology decisions resolved based on project context:

### Research Findings

See [research.md](./research.md) for detailed analysis. Key decisions:

1. **Database**: SQLite chosen
   - Built-in to Python, no installation required
   - Single-file storage matches MyAB .mbu backup approach
   - Supports ACID transactions for double-entry consistency
   - Proven for 30k transaction scale

2. **Decimal Precision**: Python `decimal.Decimal` type
   - Exact decimal arithmetic (no float rounding errors)
   - Critical for financial accuracy (Constitution Principle I)

3. **GUI Framework**: tkinter
   - Bundled with Python (zero dependencies)
   - Cross-platform (Windows, macOS, Linux)
   - Sufficient for CRUD forms and lists

4. **Testing**: pytest + pytest-cov
   - Industry standard for Python TDD
   - Excellent fixture support for test data
   - Coverage reporting for compliance verification

5. **No ORM**: Direct SQL with parameterized queries
   - Simplicity & Maintainability (Principle IV)
   - Financial calculations must be auditable
   - Avoid ORM magic/implicit behavior

## Phase 1: Design & Contracts

**Status**: ⏳ IN PROGRESS

### Data Model

See [data-model.md](./data-model.md) for complete schema.

**Key Entities**:
- `user_accounts`: User authentication and isolation
- `ledgers`: Account books with independent charts of accounts
- `accounts`: Chart of accounts (Asset/Liability/Income/Expense)
- `transactions`: Double-entry transactions with debit/credit sides

**Critical Constraints**:
- Foreign keys enforce referential integrity
- CHECK constraints enforce account type rules
- Unique constraints prevent duplicate account names within ledger
- Timestamps (created_at, modified_at) on all mutable entities

### Service Contracts

See [contracts/](./contracts/) for complete API specifications.

**Core Services**:
1. **UserAccountService**: Create/authenticate/list user accounts
2. **LedgerService**: Create/list/delete ledgers; set initial balance
3. **AccountService**: CRUD for chart of accounts; validate account types
4. **TransactionService**: Create/edit/delete transactions; calculate balances; search/filter

**Design Patterns**:
- Repository pattern for data access (isolation)
- Service layer for business rules (testability)
- Validation decorators for DI-001 compliance

### Quickstart Guide

See [quickstart.md](./quickstart.md) for developer onboarding.

Covers:
- Environment setup (Python 3.11+, venv, dependencies)
- Database initialization
- Running tests (TDD workflow)
- Architecture overview
- Code conventions

## Phase 2: Task Breakdown

**Status**: 🔜 PENDING

Run `/speckit.tasks` to generate [tasks.md](./tasks.md) with detailed implementation tasks organized by user story.

**Expected Task Structure**:
- **Phase 1: Setup** - Project initialization, dependencies
- **Phase 2: Foundational** - Database schema, base models, repositories
- **Phase 3: User Story 1** - Ledger & account management (MVP)
- **Phase 4: User Story 2** - Transaction recording & balance calculations (MVP)
- **Phase 5: User Story 3** - Search & viewing features
- **Phase 6: User Story 4** - Multiple ledgers & user accounts
- **Phase 7: Polish** - UI refinements, edge case handling, documentation

Each phase follows TDD cycle: Tests → Approval → Red → Green → Refactor

## Implementation Notes

### Critical Path (MVP = User Stories 1 + 2)

1. Database schema with double-entry enforcement
2. Ledger creation with initial cash balance
3. Account management (CRUD, type validation)
4. Transaction entry with balance updates
5. Balance calculation verification tests

### Technical Debt Prevention

- All financial calculations use `Decimal` (no float)
- Every transaction triggers balance recalculation (no caching initially)
- Input validation at service layer (before persistence)
- Comprehensive edge case tests (zero, negative, large amounts)

### Performance Optimization Strategy

- **Initial**: Simple, correct implementations (get to green)
- **Later**: Profile bottlenecks before optimizing
- **Target**: Meet SC-005 (< 100ms balance calc for < 10k transactions)
- **Technique**: SQL query optimization, indexing on foreign keys

### Testing Strategy

Per Constitution Principle II (Test-First):

1. **Contract Tests** (service boundaries):
   - Each service method has test verifying inputs/outputs
   - Focus: API contract compliance, not implementation

2. **Integration Tests** (multi-component):
   - User Story 1: Create ledger → Add account → Verify in chart
   - User Story 2: Record transaction → Verify both account balances updated
   - Critical: Double-entry balance verification

3. **Unit Tests** (isolated components):
   - Models: Validation logic, business rules
   - Validators: Amount format, date parsing, account type rules
   - Repositories: SQL query correctness (use in-memory SQLite)

4. **Edge Cases** (spec section):
   - Zero amounts, large amounts, same-account transfers
   - Future dates, overdrafts, 30k transaction limit
   - Predefined account deletion prevention

### Migration Path to Future Features

This core accounting feature provides foundation for:

- **Recurring transactions**: Add `recurrence_rule` to transactions table
- **Budget tracking**: Add `budgets` table referencing accounts
- **Reports**: Query layer over existing transaction data
- **Import/Export**: Read/write CSV using existing models
- **Cloud sync**: Serialize SQLite database to .mbu format

Clean separation (models/services/persistence/ui) enables feature additions without refactoring core.

## Next Steps

1. ✅ Constitution Check: PASSED
2. ✅ Phase 0 Research: COMPLETE
3. ⏳ Phase 1 Design: IN PROGRESS (data-model.md, contracts/, quickstart.md)
4. 🔜 Phase 2 Tasks: Run `/speckit.tasks` to generate tasks.md
5. 🔜 Implementation: Follow TDD workflow in tasks.md

## References

- [Feature Specification](./spec.md)
- [MyAB Constitution](../../.specify/memory/constitution.md)
- [MyAB Documentation](../../docs/myab-spec/)
- [Python Decimal Documentation](https://docs.python.org/3/library/decimal.html)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Accounting Principles - Double Entry](https://en.wikipedia.org/wiki/Double-entry_bookkeeping)
