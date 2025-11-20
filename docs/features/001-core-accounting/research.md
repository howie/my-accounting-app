# Research: Core Accounting System Technology Stack

**Feature**: 001-core-accounting
**Date**: 2025-11-20
**Status**: Complete

## Purpose

This document captures technology decisions for the core accounting system, resolving all "NEEDS CLARIFICATION" items from the Technical Context and ensuring alignment with the MyAB Constitution principles.

## Research Questions

1. **Database Choice**: What database technology best supports 30k transaction scale with ACID guarantees for double-entry bookkeeping?
2. **Decimal Precision**: How to ensure financial calculations have no rounding errors?
3. **GUI Framework**: What's the simplest cross-platform desktop GUI option for Python?
4. **Testing Framework**: What testing tools support TDD workflow with good fixture management?
5. **ORM vs Raw SQL**: Should we use an ORM or direct SQL for data access?

---

## Decision 1: Database Technology

### Requirement
- Support up to 30,000 transactions per ledger
- ACID transactions for double-entry consistency
- Single-file storage (matches MyAB .mbu backup approach)
- Cross-platform (Windows, macOS, Linux)
- Zero-installation (bundled with app)

### Options Evaluated

#### Option A: SQLite (Selected)
**Pros**:
- Built-in to Python (no dependencies)
- Single-file database perfect for desktop app
- ACID compliant (critical for double-entry)
- Proven performance for 30k+ records
- Cross-platform, no installation
- Battle-tested in production systems

**Cons**:
- Not suitable for concurrent multi-user (acceptable - single-user requirement)
- No built-in replication (acceptable - cloud sync via external providers)

**Performance Data**:
- 30,000 row SELECT with SUM: ~5-10ms on modern hardware
- Single INSERT: ~1ms
- Transaction (multiple INSERT): ~10-50ms depending on size

#### Option B: Embedded PostgreSQL
**Pros**:
- Full SQL feature set
- Better scalability (future-proof)

**Cons**:
- Requires installation/bundling (complexity)
- Overkill for single-user desktop
- Larger footprint

**Rejected**: Violates Simplicity & Maintainability principle (IV)

#### Option C: JSON/CSV Files
**Pros**:
- Simple, human-readable
- Easy backup

**Cons**:
- No ACID guarantees (fails Data-First Design principle I)
- No foreign key enforcement
- Poor performance at scale
- Manual index management

**Rejected**: Cannot guarantee data integrity

### Decision: SQLite

**Rationale**:
- Meets all functional requirements
- Zero dependencies (bundled with Python)
- ACID transactions essential for double-entry bookkeeping
- Single-file storage aligns with MyAB backup philosophy
- Proven performance characteristics

**References**:
- [SQLite Use Cases](https://www.sqlite.org/whentouse.html)
- [SQLite Performance](https://www.sqlite.org/speed.html)
- Python sqlite3 module: Built-in since Python 2.5

---

## Decision 2: Decimal Precision for Financial Calculations

### Requirement
- Financial calculations accurate to the cent (2 decimal places minimum)
- No floating-point rounding errors
- Support for edge cases (large amounts, many decimal places)

### Options Evaluated

#### Option A: Python `decimal.Decimal` (Selected)
**Pros**:
- Exact decimal arithmetic (no float rounding)
- Built-in to Python standard library
- Supports arbitrary precision
- Industry standard for financial calculations
- SQLite NUMERIC type maps cleanly

**Cons**:
- Slightly slower than float (acceptable for our scale)
- Requires explicit conversion from strings

**Example**:
```python
from decimal import Decimal
price = Decimal('19.99')
quantity = Decimal('3')
total = price * quantity  # Decimal('59.97') - exact!
```

#### Option B: Integer Cents
**Pros**:
- Fast (integer arithmetic)
- No rounding issues

**Cons**:
- Awkward API (user sees cents, not dollars)
- Conversion overhead at boundaries
- Limited to 2 decimal places (some use cases need more)

**Rejected**: Poor user experience, inflexible

#### Option C: Float
**Pros**:
- Fast
- Native Python type

**Cons**:
- Rounding errors (0.1 + 0.2 ≠ 0.3)
- Violates Data-First Design principle (financial accuracy)
- Not acceptable for financial software

**Rejected**: Fundamentally unsuitable for money

### Decision: Python `decimal.Decimal`

**Rationale**:
- Constitution Principle I requires financial accuracy
- Industry best practice for money calculations
- Python standard library (no dependencies)
- Clean integration with SQLite NUMERIC columns

**Implementation Notes**:
- Store as `DECIMAL(19, 2)` in SQLite (19 digits total, 2 after decimal)
- Convert to Decimal immediately on database read
- Validate string format before Decimal conversion

**References**:
- [Python Decimal Documentation](https://docs.python.org/3/library/decimal.html)
- [Floating Point Hazards](https://docs.python.org/3/tutorial/floatingpoint.html)

---

## Decision 3: GUI Framework

### Requirement
- Cross-platform (Windows, macOS, Linux)
- Simple CRUD forms (ledgers, accounts, transactions)
- List views with search/filter
- Minimal dependencies

### Options Evaluated

#### Option A: tkinter (Selected)
**Pros**:
- Bundled with Python (zero dependencies)
- Cross-platform out of the box
- Sufficient for CRUD forms and lists
- Lightweight, fast startup
- Good documentation

**Cons**:
- Less modern appearance than alternatives
- Limited built-in widgets (acceptable for MVP)

#### Option B: PyQt/PySide
**Pros**:
- Modern, polished UI
- Rich widget set
- Professional appearance

**Cons**:
- Large dependency (~50MB)
- LGPL licensing complexity (PySide)
- Overkill for simple CRUD forms

**Rejected**: Violates Simplicity principle (unnecessary complexity)

#### Option C: Web UI (Flask + HTML)
**Pros**:
- Modern web technologies
- Easier styling (CSS)

**Cons**:
- Requires bundling web server
- More complex architecture (frontend + backend)
- Offline-first requirement complicates sync

**Rejected**: Overcomplicated for desktop-only MVP

### Decision: tkinter

**Rationale**:
- Meets all UI requirements with zero dependencies
- Cross-platform compatibility proven
- Simple enough for rapid TDD iteration
- Aligns with Simplicity & Maintainability principle

**UI Components Needed**:
- Main window with menu bar
- Tree view for account lists
- Form dialogs for entry/editing
- Table widget for transaction history
- Search/filter controls

**References**:
- [tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [Real Python tkinter Tutorial](https://realpython.com/python-gui-tkinter/)

---

## Decision 4: Testing Framework

### Requirement
- Support TDD workflow (red-green-refactor)
- Fixture management for test data
- Mocking/patching for isolation
- Coverage reporting

### Options Evaluated

#### Option A: pytest + pytest-cov (Selected)
**Pros**:
- Industry standard for Python
- Excellent fixture system (`@pytest.fixture`)
- Clear, readable assertion syntax
- Plugin ecosystem (coverage, mocking)
- Parallel test execution

**Cons**:
- None significant for this use case

#### Option B: unittest (stdlib)
**Pros**:
- Built-in to Python
- No dependencies

**Cons**:
- More verbose (setUp/tearDown boilerplate)
- Weaker fixture management
- Less ergonomic assertions

**Rejected**: pytest is strictly better with minimal cost

### Decision: pytest + pytest-cov

**Rationale**:
- Best tool for TDD in Python ecosystem
- Fixture system perfect for test databases
- Coverage reporting required for constitution compliance
- Widely used (good documentation, examples)

**Test Structure**:
```
tests/
├── conftest.py           # Shared fixtures
├── contract/             # Service contract tests
├── integration/          # Multi-component tests
├── unit/                 # Isolated component tests
└── fixtures/             # Test data generators
```

**Key Fixtures**:
- `test_db`: In-memory SQLite database
- `sample_user`: User account with auth
- `sample_ledger`: Ledger with initial balance
- `sample_accounts`: Complete chart of accounts
- `sample_transactions`: Set of test transactions

**References**:
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Plugin](https://pytest-cov.readthedocs.io/)

---

## Decision 5: ORM vs Raw SQL

### Requirement
- Data access for CRUD operations
- Support for complex queries (balance calculations)
- Testability (ability to mock/fake)
- Simplicity & Maintainability (Constitution Principle IV)

### Options Evaluated

#### Option A: Raw SQL with Parameterized Queries (Selected)
**Pros**:
- Explicit, auditable queries (important for financial calculations)
- No magic/implicit behavior
- Full control over SQL for performance
- Simple to understand and debug
- Aligns with "clear over clever" principle

**Cons**:
- More boilerplate (manual mapping)
- No automatic schema migrations

**Example**:
```python
def get_account_balance(account_id: int) -> Decimal:
    query = """
        SELECT SUM(
            CASE
                WHEN debit_account_id = ? THEN -amount
                WHEN credit_account_id = ? THEN amount
                ELSE 0
            END
        ) as balance
        FROM transactions
        WHERE debit_account_id = ? OR credit_account_id = ?
    """
    cursor.execute(query, (account_id, account_id, account_id, account_id))
    return Decimal(cursor.fetchone()[0] or 0)
```

#### Option B: SQLAlchemy ORM
**Pros**:
- Automatic mapping (less boilerplate)
- Schema migrations with Alembic
- Relationship management

**Cons**:
- Complex, "magic" behavior (violates Principle IV)
- Harder to audit financial queries
- Performance overhead
- Learning curve

**Rejected**: Complexity not justified for this scale

#### Option C: Lightweight ORM (peewee)
**Pros**:
- Simpler than SQLAlchemy
- Less magic

**Cons**:
- Still adds abstraction layer
- Query builder can obscure SQL
- Not as simple as raw SQL

**Rejected**: Marginal benefit not worth dependency

### Decision: Raw SQL with Repository Pattern

**Rationale**:
- Constitution Principle IV: "Use direct, explicit code for financial calculations; avoid excessive layers"
- Financial calculations must be human-auditable (balance query should be readable SQL)
- Simple parameterized queries prevent SQL injection
- Repository pattern provides testability without ORM complexity

**Implementation Pattern**:
```python
class TransactionRepository:
    def __init__(self, db_connection):
        self.conn = db_connection

    def create(self, transaction: Transaction) -> int:
        query = """
            INSERT INTO transactions
            (date, type, debit_account_id, credit_account_id, amount, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = self.conn.execute(query, (
            transaction.date,
            transaction.type,
            transaction.debit_account_id,
            transaction.credit_account_id,
            str(transaction.amount),  # Decimal to string
            transaction.description
        ))
        return cursor.lastrowid
```

**References**:
- [Python sqlite3 Tutorial](https://docs.python.org/3/library/sqlite3.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)

---

## Summary of Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Python 3.11+ | Project requirement, good stdlib, cross-platform |
| **Database** | SQLite | ACID guarantees, zero-install, proven at scale |
| **Decimal Math** | `decimal.Decimal` | Financial accuracy, no rounding errors |
| **GUI** | tkinter | Zero dependencies, cross-platform, sufficient features |
| **Testing** | pytest + pytest-cov | Industry standard, excellent fixtures, coverage reports |
| **Data Access** | Raw SQL + Repository | Simplicity, auditability, no ORM magic |

## Dependencies

### Production
```
# requirements.txt
# (No external dependencies - all standard library)
```

### Development
```
# requirements-dev.txt
pytest>=7.4.0
pytest-cov>=4.1.0
```

## Next Steps

1. ✅ Technology stack finalized
2. → Create data-model.md (database schema)
3. → Create service contracts
4. → Create quickstart.md (developer setup guide)
5. → Update agent context with stack decisions

## Constitution Compliance

All technology decisions reviewed against five core principles:

- ✅ **Principle I (Data-First)**: SQLite ACID + Decimal precision ensure financial accuracy
- ✅ **Principle II (Test-First)**: pytest enables TDD workflow
- ✅ **Principle III (Financial Accuracy)**: Decimal + double-entry schema enforce correctness
- ✅ **Principle IV (Simplicity)**: No ORM, minimal dependencies, clear code
- ✅ **Principle V (Cross-Platform)**: All choices work on Windows/macOS/Linux
