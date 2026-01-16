# Checklist: Business Rules & Edge Case Requirements (009-reports)

**Feature**: 009-reports
**Purpose**: Unit Tests for Requirements (Business Rules & Edge Cases dimension)
**Audience**: Author (Self-Review)
**Created**: 2026-01-16
**Depth**: Deep Dive

## Requirement Completeness

- [x] CHK001 Are requirements for the treatment of **Closed Accounts** defined? [Spec §Business Rules]
- [x] CHK002 Is the behavior for **Zero-Balance Accounts** explicitly specified? [Spec §Business Rules]
- [x] CHK003 Are requirements defined for handling **Future Dates** in a Balance Sheet request? [Spec §Business Rules]
- [x] CHK004 Does the spec define how to handle **Account Hierarchy Changes**? [Spec §Business Rules]
- [x] CHK005 Are requirements specified for **Backdated Transactions**? [Spec §Business Rules]
- [x] CHK006 Is the **Currency Precision** requirement for aggregation defined? [Spec §Business Rules]

## Requirement Clarity

- [x] CHK007 Are the **Income Statement Boundaries** (Start Date and End Date) explicitly defined as inclusive or exclusive? [Clarity, Spec §Business Rules]
- [x] CHK008 Is the term **"Net Income"** clearly distinguished from **"Net Worth"** in the requirements? [Clarity, Spec §FR-1/FR-2]
- [x] CHK009 Is the calculation for **Equity** clearly documented as a derived value (`Assets - Liabilities`) or as a sum of specific Equity accounts? [Clarity, Data-Model.md]
- [x] CHK010 Are the **Transaction Types** (EXPENSE, INCOME, TRANSFER) explicitly mapped to their effect on each report type? [Clarity, Research.md]

## Requirement Consistency

- [ ] CHK011 Does the **Debit/Credit logic** for report aggregation align with the core accounting principles defined in `001-core-accounting`? [Consistency, Research.md]
- [ ] CHK012 Are the account type groupings (Asset, Liability, Income, Expense) consistent across all report definitions? [Consistency, Spec §4.1]

## Scenario & Edge Case Coverage

- [ ] CHK013 Are requirements defined for a **Single Account Transaction** (if ever allowed by error)? (e.g., How does the report handle an unbalanced transaction? [Edge Case, Gap])
- [ ] CHK014 Is the behavior specified for a **Leap Year** date range in the Income Statement? [Edge Case, Gap]
- [ ] CHK015 Are requirements defined for scenarios where a **Parent Account** has its own transactions (forbidden by logic, but possible in DB)? [Edge Case, Gap]
- [ ] CHK016 Is the behavior specified for **Multi-Ledger Aggregation** (if a user has multiple ledgers)? [Coverage, Gap]

## Acceptance Criteria Quality

- [ ] CHK017 Can the requirement for **"Financial Accuracy"** be objectively verified with a specific set of sample transactions? [Measurability, Plan.md]
- [ ] CHK018 Is the success criteria for **"Hierarchical Totals"** defined with a mathematical formula? [Measurability]

## Dependencies & Assumptions

- [ ] CHK019 Is the assumption that **SQLite's Decimal handling** is sufficient for 30,000 transactions validated in the requirements? [Assumption, Research.md]
- [ ] CHK020 Are dependencies on the **Account Metadata** (is_system, parent_id) clearly documented for report grouping? [Dependency, Research.md]
