# Checklist: API Contract & Performance Requirements (009-reports)

**Feature**: 009-reports
**Purpose**: Unit Tests for Requirements (API & Performance dimension)
**Audience**: QA / Product Owner
**Created**: 2026-01-16

## Requirement Completeness

- [x] CHK001 Are error response schemas defined for invalid date formats (e.g., 400 Bad Request)? [Completeness, Contracts/openapi.yaml]
- [x] CHK002 Is the behavior specified when a request is made for a date with no transactions? [Spec §Error Handling]
- [x] CHK003 Are requirements defined for the maximum date range allowed in an Income Statement request? [Spec §Business Rules]
- [x] CHK004 Does the spec define the behavior for accounts that were deleted but have historical transactions? [Spec §Business Rules]
- [ ] CHK005 Are requirements defined for handling multi-currency scenarios (if applicable)? [Gap] (N/A - App is single currency for now)

## Requirement Clarity

- [x] CHK006 Is the decimal precision for all API response fields explicitly defined (e.g., 2 decimal places)? [Clarity, Data-Model.md]
- [ ] CHK007 Is the sort order of `ReportEntry` items at the same level (alphabetical vs. manual sort order) defined? [Clarity, Plan.md]
- [x] CHK008 Is the calculation logic for "Equity" explicitly documented to ensure alignment with "Total Assets - Total Liabilities"? [Clarity, Data-Model.md]
- [ ] CHK009 Does the contract define whether `account_id` is mandatory for leaf nodes in the hierarchy? [Clarity, Contracts/openapi.yaml]

## Requirement Consistency

- [ ] CHK010 Do the field names in `openapi.yaml` (e.g., `total_assets`) match the naming conventions in `data-model.md`? [Consistency]
- [ ] CHK011 Are the date format requirements (ISO 8601) consistent across both Balance Sheet and Income Statement endpoints? [Consistency]

## Performance Requirements (Quality)

- [ ] CHK012 Is the "Report generation < 200ms" goal quantified with a specific dataset size (e.g., at 30,000 transactions)? [Clarity, Plan.md]
- [ ] CHK013 Are latency requirements defined for the worst-case scenario (e.g., first request after many updates)? [Gap]
- [ ] CHK014 Is there a maximum payload size requirement for reports with deeply nested hierarchies? [Gap]

## Acceptance Criteria Quality

- [ ] CHK015 Can the requirement "Must maintain double-entry accounting integrity" be objectively verified through API response validation? [Measurability, Plan.md]
- [ ] CHK016 Are the success criteria for the hierarchical structure (e.g., level 0 vs level 1) measurable in the JSON schema? [Measurability]

## Scenario & Edge Case Coverage

- [ ] CHK017 Is the behavior defined for Future Dates (requests for dates later than today)? [Edge Case, Gap]
- [ ] CHK018 Are requirements specified for "Zero State" (new ledger with zero transactions)? [Coverage, Gap]
- [ ] CHK019 Does the spec define how to handle accounts with a zero balance in the report (hide vs. show)? [Coverage, Gap]
- [ ] CHK020 Are requirements defined for partial data loading or timeouts if the aggregation takes too long? [Exception Flow, Gap]
