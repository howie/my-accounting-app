# Feature Specification: Core Accounting System

**Feature Branch**: `001-core-accounting`
**Created**: 2025-11-20
**Status**: Draft
**Input**: User description: "core accounting design @docs/myab-spec/README.md"

## Clarifications

### Session 2025-11-20

- Q: How do users specify account type when creating accounts - do they manually type prefixes or select from a dropdown? → A: Users select account type from dropdown (Asset/Liability/Income/Expense), system auto-adds prefix ("A-", "L-", etc.) to the account name
- Q: What happens when account balance would become negative (overdraft scenario)? → A: Allow negative balances for Asset/Liability accounts but display warning indicator (e.g., red text, warning icon)
- Q: What decimal precision should the system support for financial amounts and how should rounding be handled? → A: Support exactly 2 decimal places with standard rounding (banker's rounding to nearest even)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Ledger and Initial Setup (Priority: P1)

A user needs to start tracking their personal finances by creating a ledger (account book) and setting up the chart of accounts.

**Why this priority**: This is the foundational capability - without a ledger and account categories, no financial tracking can occur. It represents the minimum viable product.

**Independent Test**: Can be fully tested by creating a new ledger, setting initial cash balance, and verifying that predefined accounts (Cash, Equity) exist and custom accounts can be added.

**Acceptance Scenarios**:

1. **Given** a new user opens the application, **When** they create a new ledger with name "2024 Budget" and initial cash of 10,000, **Then** the system creates the ledger with Cash account showing balance of 10,000
2. **Given** a ledger exists, **When** user adds a new account "Bank Account" and selects type Asset from dropdown, **Then** the system creates account "A-Bank Account" (with auto-added prefix) and it appears in the account list
3. **Given** a ledger with predefined Cash and Equity accounts, **When** user attempts to delete either account, **Then** system prevents deletion and shows error message
4. **Given** user creates accounts of different types using the type dropdown, **When** viewing account list, **Then** accounts display with auto-added prefixes ("A-", "L-", "I-", "E-") and are categorized correctly

---

### User Story 2 - Record Basic Transactions (Priority: P1)

A user needs to record daily financial transactions including expenses, income, and transfers between accounts.

**Why this priority**: Recording transactions is the core purpose of accounting software. Without this, the system provides no value. This is the second critical piece of the MVP.

**Independent Test**: Can be fully tested by creating expense, income, and transfer transactions and verifying that account balances update correctly according to double-entry bookkeeping rules.

**Acceptance Scenarios**:

1. **Given** a ledger with Cash account having 10,000 balance, **When** user records expense of 50 from Cash to "E-Food", **Then** Cash balance decreases to 9,950 and Food expense shows 50
2. **Given** user records income of 30,000 from "I-Salary" to "A-Bank Account", **When** viewing account balances, **Then** Bank Account shows increase of 30,000 and Salary income shows 30,000
3. **Given** user has 5,000 in Cash and 10,000 in Bank, **When** user transfers 2,000 from Cash to Bank, **Then** Cash shows 3,000 and Bank shows 12,000 (net assets unchanged)
4. **Given** user records a transaction, **When** they immediately double-click the transaction, **Then** they can edit any field (date, amount, accounts, description) and changes are saved
5. **Given** Cash account has 100 balance, **When** user records expense of 150, **Then** Cash balance becomes -50 and displays with warning indicator (red text or warning icon)

---

### User Story 3 - View Account Balances and Transaction History (Priority: P2)

A user needs to view current account balances and search through transaction history to understand their financial position.

**Why this priority**: While essential for usefulness, viewing can come after basic recording capability. Users can still add transactions without sophisticated viewing features.

**Independent Test**: Can be independently tested by creating various transactions and verifying that balances reflect all transactions correctly and search/filter features return expected results.

**Acceptance Scenarios**:

1. **Given** multiple transactions have been recorded, **When** user views the account list, **Then** each account shows its current balance calculated from all transactions
2. **Given** 50 transactions exist, **When** user searches by description keyword "lunch", **Then** system displays only transactions containing "lunch" in description field
3. **Given** transactions span 3 months, **When** user filters by date range (March 1-31), **Then** only March transactions are displayed
4. **Given** user selects account "E-Food", **When** viewing transactions for that account, **Then** only transactions involving the Food expense account are shown

---

### User Story 4 - Multiple Ledgers and User Accounts (Priority: P3)

A user wants to separate different financial contexts (personal vs. business, different years, different family members) using multiple ledgers or user accounts.

**Why this priority**: This is a convenience and organizational feature that enhances the basic product but isn't essential for initial financial tracking.

**Independent Test**: Can be tested independently by creating multiple ledgers under one user account and verifying complete data isolation between them.

**Acceptance Scenarios**:

1. **Given** a user account exists, **When** user creates ledgers "2024 Personal" and "2024 Business", **Then** each ledger has independent account charts and transaction lists
2. **Given** two ledgers exist with same account name "A-Cash", **When** user records transaction in one ledger, **Then** the other ledger's Cash account is unaffected
3. **Given** multiple ledgers exist, **When** user switches between ledgers, **Then** system loads the correct accounts and transactions for the selected ledger
4. **Given** user creates ledger "Japan Trip" with initial cash 50,000, **When** trip ends and ledger is deleted, **Then** system prompts for confirmation and permanently removes the ledger data

---

### Edge Cases

- What happens when user attempts to record a transaction with zero amount?
- How does system handle very large amounts (e.g., 999,999,999)?
- What happens when user tries to transfer between the same account (A-Cash to A-Cash)?
- How does system handle transactions with future dates?
- Negative balances (overdrafts): System allows Asset/Liability accounts to have negative balances and displays visual warning indicators (red text or warning icon) to alert users
- How does system prevent deletion of accounts that have associated transactions?
- What happens when user creates more than 30,000 transactions (database limit)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support creation of multiple ledgers per user account, each with independent chart of accounts and transaction records
- **FR-002**: System MUST enforce double-entry bookkeeping for all transactions (every transaction affects exactly two accounts with equal amounts)
- **FR-003**: System MUST support four account types: Asset (A), Liability (L), Income (I), Expense (E)
- **FR-003a**: System MUST automatically prepend the appropriate prefix (A-, L-, I-, E-) to account names based on the user-selected account type from dropdown
- **FR-004**: System MUST prevent deletion of two predefined accounts: "Cash" (Asset) and "Equity" (Asset)
- **FR-005**: System MUST support three transaction types: Expense (Asset/Liability → Expense), Income (Income → Asset/Liability), Transfer (Asset/Liability → Asset/Liability)
- **FR-006**: System MUST validate transaction rules: Expense must debit Expense account and credit Asset/Liability; Income must debit Asset/Liability and credit Income; Transfer must involve two different Asset/Liability accounts
- **FR-007**: Users MUST be able to edit existing transactions with all field modifications reflected in account balances immediately
- **FR-008**: Users MUST be able to delete single or multiple transactions with confirmation prompt
- **FR-009**: System MUST recalculate all affected account balances automatically when transactions are added, edited, or deleted
- **FR-010**: System MUST support searching transactions by description keyword, account, date range, or tag/mark
- **FR-011**: System MUST store transaction metadata: date, transaction type, debit account, credit account, amount, description, invoice number (optional)
- **FR-012**: System MUST limit total transactions per ledger to 30,000 records
- **FR-013**: System MUST support negative amounts for special cases (e.g., refunds, returns)
- **FR-014**: Users MUST be able to set initial balance when creating a new ledger
- **FR-015**: System MUST support account renaming, copying, and deletion (with transaction validation)
- **FR-016**: System MUST allow Asset and Liability accounts to have negative balances and display visual warning indicators (red text, warning icon) when balance is negative

### Data Integrity Requirements *(required for features modifying financial data)*

For features that create, modify, or delete financial transactions:

- **DI-001**: System MUST validate all financial amounts are numeric and support exactly 2 decimal places; all calculations MUST use banker's rounding (round to nearest even) to prevent accumulation errors
- **DI-002**: System MUST maintain audit trail showing which transactions modified account balances (implicit through transaction log)
- **DI-003**: System MUST enforce double-entry bookkeeping where total debits equal total credits for every transaction
- **DI-004**: System MUST require confirmation before deleting transactions or ledgers to prevent silent data loss
- **DI-005**: System MUST ensure all account balance calculations are traceable to source transactions

### Key Entities *(include if feature involves data)*

- **User Account**: Represents a unique user with password protection. Multiple user accounts can exist in one installation. Each user account contains multiple ledgers. Attributes: account name (alphanumeric), password (alphanumeric only).

- **Ledger (Account Book)**: A container for financial records representing a specific tracking context (e.g., personal finances for 2024, business accounts, travel budget). Each ledger has independent chart of accounts and transaction list. Attributes: ledger name (supports Unicode), initial cash amount, creation date.

- **Account (Category)**: A classification category in the chart of accounts. Must be one of four types: Asset (things you own), Liability (things you owe), Income (increases net worth), Expense (decreases net worth). When creating an account, users select the type from a dropdown and enter the account name; the system automatically prepends the appropriate prefix (A-, L-, I-, E-) to the name. Attributes: account name (includes system-added prefix), account type, current balance (calculated), initial balance (for Asset/Liability only).

- **Transaction**: A financial event recorded using double-entry bookkeeping. Every transaction has exactly two sides (debit and credit) affecting two different accounts. Attributes: transaction date, transaction type (expense/income/transfer), debit account, credit account, amount (exactly 2 decimal places), description, optional invoice number.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new ledger and record their first transaction in under 3 minutes
- **SC-002**: System maintains data integrity for ledgers containing up to 30,000 transactions without balance calculation errors
- **SC-003**: Users can find a specific transaction using search within 10 seconds for ledgers with up to 5,000 transactions
- **SC-004**: 95% of users successfully create their first expense transaction without viewing help documentation
- **SC-005**: Account balance calculations complete instantly (under 100ms) after transaction entry for typical use (under 10,000 transactions)
- **SC-006**: System prevents 100% of invalid transactions that would violate double-entry bookkeeping rules
- **SC-007**: Users can manage multiple ledgers (e.g., personal + business) without cross-contamination of financial data

## Assumptions

- **A-001**: Users understand basic accounting concepts (assets, liabilities, income, expenses) or can learn them from brief documentation
- **A-002**: Single currency per ledger is acceptable; users requiring multi-currency will create separate ledgers per currency
- **A-003**: Users will manually backup their data; automatic cloud sync is handled through external cloud storage providers
- **A-004**: Transaction description field supports up to 125 characters for display purposes
- **A-005**: Desktop application is primary target; web/mobile access will be addressed in future features
- **A-006**: Users accept that editing historical transactions will immediately affect current balances (no audit lock for closed periods)
- **A-007**: System will operate on single-user mode; no concurrent multi-user editing required

## Constraints

- **C-001**: Maximum 30,000 transactions per ledger (database engine limitation)
- **C-002**: User account passwords restricted to alphanumeric characters only (no special symbols)
- **C-003**: Predefined accounts "Cash" and "Equity" cannot be deleted (system requirement)
- **C-004**: Single currency per ledger (architecture limitation)
- **C-005**: No undo/redo functionality; deleted transactions cannot be recovered except from backups

## Out of Scope

The following features are explicitly NOT included in this core accounting feature:

- Recurring/scheduled transactions (addressed in separate feature)
- Installment payment tracking (addressed in separate feature)
- Budget tracking and alerts (addressed in separate feature)
- Financial reports and charts (addressed in separate feature)
- Data import/export (CSV, HTML) (addressed in separate feature)
- Backup and restore functionality (addressed in separate feature)
- Invoice lottery checking (addressed in separate feature)
- Mobile web access (addressed in separate feature)
- Tag/mark system for categorizing transactions (addressed in separate feature)
- Quick-entry templates for frequent transactions (addressed in separate feature)
- Bulk edit operations (addressed in separate feature)
- Amount calculator in entry fields (addressed in separate feature)

## Dependencies

- None - this is the foundational feature that other features depend on

## References

- Official MyAB documentation: https://www.devon.riceball.net/display.php?file=w04_00
- Internal specification documents: docs/myab-spec/
  - 00-overview.md: System overview and core concepts
  - 01-basic-setup.md: Account and ledger setup
  - 02-transaction-management.md: Transaction recording
  - 09-business-rules.md: System constraints and rules
