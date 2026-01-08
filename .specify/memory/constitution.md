<!--
═══════════════════════════════════════════════════════════════════════════════
SYNC IMPACT REPORT - Constitution v1.0.0
═══════════════════════════════════════════════════════════════════════════════

Version Change: [INITIAL] → 1.0.0
Reason: Initial constitution creation for MyAB (我的記帳簿) accounting application

Modified Principles: N/A (initial creation)

Added Sections:
- I. Data-First Design (NON-NEGOTIABLE)
  → Every feature must preserve financial accuracy and maintain audit trails
  → Data loss prevention and validation required at all boundaries

- II. Test-First Development (NON-NEGOTIABLE)
  → TDD mandatory: Tests → Approval → Red → Green → Refactor
  → Special requirements for financial features (contract, integration, edge cases)

- III. Financial Accuracy & Audit Trail
  → Double-entry bookkeeping enforcement
  → Immutable transaction history with change logging

- IV. Simplicity & Maintainability
  → YAGNI principles, clear over clever code
  → Financial calculations must be human-auditable

- V. Cross-Platform Consistency
  → Identical calculations across Windows, macOS, web/mobile
  → Data format compatibility and conflict resolution

Removed Sections: N/A (initial creation)

Templates Updated:
✅ .specify/templates/plan-template.md
   - Added comprehensive Constitution Check section with all 5 principles
   - Each principle has checkboxes and violation tracking
   - Added PASS/CONDITIONAL PASS/FAIL assessment gate

✅ .specify/templates/spec-template.md
   - Added "Data Integrity Requirements" section
   - 5 mandatory checks for features modifying financial data (DI-001 through DI-005)
   - Aligned with Principle I (Data-First Design)

✅ .specify/templates/tasks-template.md
   - Changed tests from OPTIONAL to MANDATORY (per Principle II)
   - Added test approval gates before implementation
   - Added "verify tests FAIL" gate (red phase of TDD)
   - Expanded implementation tasks to include validation and audit trails
   - Added "tests PASS" and "refactor" tasks to complete TDD cycle
   - Updated all 3 user story sections consistently

Templates Reviewed (No Changes Needed):
✅ .specify/templates/checklist-template.md - Generic template, no constitution-specific refs
✅ .specify/templates/agent-file-template.md - Generic template, no constitution-specific refs

Additional Files Reviewed:
✅ CLAUDE.md - Already references Python project, no constitution conflicts
✅ README.md - Minimal placeholder, no conflicts
✅ docs/myab-spec/ - User documentation, not affected by dev constitution

Follow-up TODOs:
- RATIFICATION_DATE: 2025-11-20 (today, initial adoption)
- LAST_AMENDED_DATE: 2025-11-20 (same as ratification for v1.0.0)
- Future consideration: Add specific principle for cloud sync/data migration as app matures
- Future consideration: May need security principle as payment integration develops

═══════════════════════════════════════════════════════════════════════════════
-->

# MyAB Constitution

## Core Principles

### I. Data-First Design (NON-NEGOTIABLE)

Data integrity is paramount in financial software. Every feature MUST:

- **Preserve financial accuracy**: All calculations must be verifiable and correct to the cent
- **Maintain audit trails**: Every transaction modification must be logged with timestamp and reason
- **Prevent data loss**: No operation may delete or modify financial records without explicit user confirmation and backup
- **Enforce data validation**: All inputs must be validated before persistence (amounts, dates, account references)
- **Support data recovery**: All destructive operations must be reversible through backup/restore mechanisms

**Rationale**: Financial data is irreplaceable. Users trust this application with their financial history. A single data corruption or calculation error can undermine years of records and user confidence.

### II. Test-First Development (NON-NEGOTIABLE)

TDD is mandatory for all feature development. The workflow MUST be:

1. **Tests written FIRST** - Before any implementation code
2. **User approval** - Tests reviewed and approved by stakeholder
3. **Tests FAIL** - Verify tests catch the absence of the feature
4. **Implementation** - Write minimum code to pass tests
5. **Refactor** - Improve code while maintaining green tests

**Special Requirements for Financial Features**:

- Contract tests for all API/service boundaries
- Integration tests for multi-account transactions
- Edge case tests for rounding, currency conversion, date boundaries
- Regression tests for all reported bugs

**Rationale**: Financial software errors can have serious consequences. TDD ensures features are specified correctly before implementation and provides regression protection for this data-critical application.

### III. Financial Accuracy & Audit Trail

All financial operations MUST maintain verifiable accuracy:

- **Double-entry bookkeeping**: Every transaction must balance (debits = credits)
- **Immutable history**: Posted transactions cannot be silently modified (only void-and-reenter)
- **Calculation transparency**: All computed values (balances, totals, reports) must be traceable to source transactions
- **Timestamp precision**: Record creation time, modification time, and business date separately
- **Change logging**: Maintain who, what, when, why for all data modifications

**Rationale**: Accounting principles require complete audit trails. Users must be able to verify every number in every report back to original transactions.

### IV. Simplicity & Maintainability

Complexity is the enemy of correctness in financial software:

- **YAGNI**: Implement only requested features, not anticipated "might need" functionality
- **Clear over clever**: Prefer readable code over performance optimizations unless profiling proves necessity
- **Minimize abstractions**: Use direct, explicit code for financial calculations; avoid excessive layers
- **No premature optimization**: Get it correct first, fast second
- **Document complex business rules**: If accounting logic is non-obvious, include reference to accounting principle or regulation

**Rationale**: Financial calculations must be auditable by humans. Overly abstract or "clever" code makes bugs harder to find and fix, increasing risk of financial errors.

### V. Cross-Platform Consistency

MyAB supports Windows, macOS, and web/mobile platforms. MUST maintain:

- **Identical calculation results**: Same transaction data produces identical reports on all platforms
- **Data format compatibility**: Desktop and web versions read/write compatible database formats
- **Feature parity awareness**: Clearly document which features are platform-specific vs. universal
- **Consistent UX patterns**: Similar workflows across platforms (while respecting platform conventions)
- **Synchronized data**: Cloud sync must maintain transaction ordering and conflict resolution

**Rationale**: Users may access their financial data from multiple devices. Inconsistent calculations or data loss during sync would destroy trust in the application.

## Development Workflow

### Feature Development Process

1. **Specification**: Document user scenarios with acceptance criteria
2. **Test Design**: Write tests covering all scenarios and edge cases
3. **Test Approval**: Review tests with stakeholder/user
4. **Implementation**: Write minimum code to pass tests
5. **Verification**: Ensure all tests pass, no data integrity violations
6. **Documentation**: Update user docs and accounting logic references

### Code Review Requirements

All code changes MUST be reviewed for:

- ✅ Data integrity preservation (Principle I)
- ✅ Test coverage completeness (Principle II)
- ✅ Audit trail compliance (Principle III)
- ✅ Code clarity (Principle IV)
- ✅ Cross-platform compatibility (Principle V)

### Quality Gates

Before merging to main branch:

- All tests pass (unit, integration, contract)
- No calculation regression (existing reports unchanged)
- Data migration tested (if schema changes)
- Manual testing on target platforms
- Documentation updated

## Technology Constraints

### Database Requirements

- Single database limit: 30,000 transactions (documented limit)
- Backup format: .mbu (proprietary)
- Export formats: CSV, HTML (human-readable)
- Must support SQLite for desktop, compatible format for web

### Platform Support

- **Windows**: MyAB desktop application
- **macOS**: MacMoney variant
- **Web/Mobile**: Browser-based access (iPhone/Android)
- **Cloud Integration**: Dropbox, Google Drive, OneDrive

### Performance Standards

- Report generation: < 2 seconds for datasets up to 30,000 transactions
- Transaction entry: < 100ms response time
- Backup/restore: < 10 seconds for full database
- Search/filter: < 500ms for complex queries

## Governance

### Constitution Authority

This constitution supersedes all other development practices. When in conflict, constitution principles take precedence.

### Amendment Process

Constitution changes require:

1. **Proposal**: Document proposed change with rationale
2. **Impact Analysis**: Identify affected code, tests, documentation
3. **Review**: Discuss with all stakeholders
4. **Version Bump**: Follow semantic versioning (MAJOR.MINOR.PATCH)
5. **Migration Plan**: Update all dependent templates and docs
6. **Approval**: Must be approved before implementation

### Versioning Policy

- **MAJOR**: Breaking change to principles (e.g., removing TDD requirement)
- **MINOR**: New principle added or significant expansion of existing principle
- **PATCH**: Clarifications, wording improvements, non-semantic changes

### Compliance Review

- All PRs must verify constitution compliance
- Quarterly review of adherence to principles
- Violations must be documented and justified or remediated
- Repeated violations trigger constitution review

### Runtime Guidance

For day-to-day development guidance, consult `CLAUDE.md` in repository root. That file provides AI assistant instructions while this constitution defines non-negotiable project principles.

---

**Version**: 1.0.0 | **Ratified**: 2025-11-20 | **Last Amended**: 2025-11-20
