# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/docs/features/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with all five core principles from `.specify/memory/constitution.md`:

### I. Data-First Design (NON-NEGOTIABLE)
- [ ] Does this feature preserve financial accuracy (calculations correct to the cent)?
- [ ] Are audit trails maintained (all modifications logged with timestamp/reason)?
- [ ] Is data loss prevented (confirmations + backups for destructive operations)?
- [ ] Is input validation enforced (amounts, dates, account references)?
- [ ] Are destructive operations reversible?

**Violations**: [List any violations with justification, or write "None"]

### II. Test-First Development (NON-NEGOTIABLE)
- [ ] Will tests be written BEFORE implementation?
- [ ] Will tests be reviewed/approved before coding?
- [ ] Are contract tests planned for service boundaries?
- [ ] Are integration tests planned for multi-account transactions?
- [ ] Are edge case tests planned (rounding, currency, date boundaries)?

**Violations**: [List any violations with justification, or write "None"]

### III. Financial Accuracy & Audit Trail
- [ ] Does design maintain double-entry bookkeeping (debits = credits)?
- [ ] Are transactions immutable once posted (void-and-reenter only)?
- [ ] Are calculations traceable to source transactions?
- [ ] Are timestamps tracked (created, modified, business date)?
- [ ] Is change logging implemented (who, what, when, why)?

**Violations**: [List any violations with justification, or write "None"]

### IV. Simplicity & Maintainability
- [ ] Is this feature actually needed (not speculative)?
- [ ] Is the design clear over clever (human-auditable)?
- [ ] Are abstractions minimized (especially for financial calculations)?
- [ ] Are complex business rules documented with accounting references?

**Violations**: [List any violations with justification, or write "None"]

### V. Cross-Platform Consistency
- [ ] Will calculations produce identical results across platforms?
- [ ] Is data format compatible between desktop and web?
- [ ] Are platform-specific features clearly documented?
- [ ] Do workflows follow consistent UX patterns?
- [ ] Does cloud sync maintain transaction ordering?

**Violations**: [List any violations with justification, or write "None"]

**Overall Assessment**: [PASS / CONDITIONAL PASS / FAIL]
- If CONDITIONAL PASS or FAIL, document required changes before proceeding

## Project Structure

### Documentation (this feature)

```text
docs/features/[###-feature]/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
├── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
└── issues/              # Issue tracking for this feature
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
