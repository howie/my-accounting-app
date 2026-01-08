# Feature Specification: Settings & Account Management

**Feature Branch**: `003-settings-account-management`
**Created**: 2026-01-07
**Status**: In Progress (v1.1.0 - Collapsible Account Tree)
**Version**: 1.1.0
**Completed**: 2026-01-07 (v1.0.0)
**Input**: Settings page and account (科目) management functionality as defined in ROADMAP.md

## Clarifications

### Session 2026-01-07

- Q: Where should user preferences (language, theme) be stored? → A: Browser local storage only (per-device, no sync)
- Q: What should happen when deleting an account that has transactions? → A: Offer to reassign all transactions to a selected replacement account before deletion

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add New Account to Ledger (Priority: P1)

As a user, I want to add new accounts (科目) to my ledger so I can organize and categorize my financial transactions according to my personal needs.

**Why this priority**: Account creation is the foundational capability - without being able to add accounts, users cannot customize their chart of accounts to match their financial situation.

**Independent Test**: Can be fully tested by creating a new account in any category (Asset, Liability, Income, Expense) and verifying it appears in the sidebar account tree.

**Acceptance Scenarios**:

1. **Given** I am viewing the account management page, **When** I click "Add Account" and enter an account name and select a parent account, **Then** the new account is created as a child of the selected parent and appears in the account tree.
2. **Given** I am adding a new account, **When** I select one of the four account types (Asset, Liability, Income, Expense), **Then** the account is created under the correct category.
3. **Given** I am adding a new account, **When** I try to create an account with a name that already exists under the same parent, **Then** I receive an error message and the account is not created.

---

### User Story 2 - Edit Existing Account (Priority: P1)

As a user, I want to edit account names so I can correct mistakes or update accounts as my financial organization evolves.

**Why this priority**: Users frequently need to rename accounts to fix typos or better reflect their purpose. This is essential for maintaining an organized chart of accounts.

**Independent Test**: Can be fully tested by editing any existing account name and verifying the change persists across the application.

**Acceptance Scenarios**:

1. **Given** I am viewing an account in the account management page, **When** I click "Edit" and change the account name, **Then** the account name is updated everywhere it appears (sidebar, transaction lists, etc.).
2. **Given** I am editing an account name, **When** I try to rename it to a name that already exists under the same parent, **Then** I receive an error message and the rename is rejected.

---

### User Story 3 - Delete Account (Priority: P2)

As a user, I want to delete accounts I no longer need so I can keep my chart of accounts clean and relevant.

**Why this priority**: Important for maintaining a clean account structure, but less frequently needed than creation and editing.

**Independent Test**: Can be fully tested by deleting an account with no transactions and verifying it is removed from the account tree.

**Acceptance Scenarios**:

1. **Given** I am viewing an account with no associated transactions, **When** I click "Delete" and confirm, **Then** the account is permanently removed from the ledger.
2. **Given** I am viewing an account that has associated transactions, **When** I click "Delete", **Then** I am prompted to select a replacement account to reassign all transactions to before deletion proceeds.
3. **Given** I am reassigning transactions during account deletion, **When** I select a valid replacement account and confirm, **Then** all transactions are moved to the replacement account and the original account is deleted.
4. **Given** I am viewing a parent account with child accounts, **When** I try to delete it, **Then** I see a warning that the account has children and cannot be deleted until children are removed or moved.

---

### User Story 4 - Organize Accounts with Drag-and-Drop (Priority: P2)

As a user, I want to reorder accounts by dragging them so I can arrange my accounts in a logical order that matches how I think about my finances.

**Why this priority**: Improves usability by letting users personalize their view, but the default order is functional.

**Independent Test**: Can be fully tested by dragging one account above another and verifying the new order persists after page refresh.

**Acceptance Scenarios**:

1. **Given** I am on the account management page, **When** I drag an account to a new position within its parent, **Then** the account moves to that position and the new order is saved.
2. **Given** I am dragging an account, **When** I drag it onto another account, **Then** it becomes a child of that account (supporting hierarchical restructuring).
3. **Given** I have reordered accounts, **When** I navigate to the sidebar, **Then** the sidebar reflects the new account order.

---

### User Story 5 - Access Settings from Sidebar (Priority: P1)

As a user, I want to access Settings from the sidebar menu so I can easily find and manage application settings including account management.

**Why this priority**: Entry point to all settings functionality - without this, users cannot access any settings features.

**Independent Test**: Can be fully tested by clicking the Settings menu item in the sidebar and verifying the Settings page loads.

**Acceptance Scenarios**:

1. **Given** I am on any page in the application, **When** I click "Settings" in the sidebar menu, **Then** I am navigated to the Settings page.
2. **Given** I am on the Settings page, **When** I view the navigation options, **Then** I see "Account Management" as an available section.

---

### User Story 6 - Support 3-Level Account Hierarchy (Priority: P2)

As a user, I want to create accounts up to 3 levels deep (e.g., Deposits > LineBank > Foreign Currency Account) so I can organize complex financial structures.

**Why this priority**: Enables sophisticated organization for users with complex finances, but the basic 2-level structure works for most users.

**Independent Test**: Can be fully tested by creating a grandchild account (3rd level) and verifying it displays correctly in the tree.

**Acceptance Scenarios**:

1. **Given** I have a 2-level account hierarchy, **When** I add a new account as a child of a 2nd-level account, **Then** a 3rd-level account is created successfully.
2. **Given** I have a 3-level hierarchy, **When** I try to add a child to a 3rd-level account, **Then** I receive a message that maximum depth (3 levels) has been reached.
3. **Given** I am viewing the sidebar, **When** accounts have 3 levels, **Then** all 3 levels are displayed with appropriate indentation.

---

### User Story 6a - Collapsible Account Tree with Aggregated Balances (Priority: P1)

As a user, I want parent accounts in the sidebar to show aggregated balances of their children, and I want to be able to collapse/expand parent accounts so I can get a quick overview without seeing all details.

**Why this priority**: Essential for usability with hierarchical accounts - users need to see totals at a glance and drill down only when needed.

**Independent Test**: Can be fully tested by checking that a parent account shows the sum of all child balances, and verifying the collapse/expand functionality hides/shows children.

**Acceptance Scenarios**:

1. **Given** I am viewing the sidebar with accounts, **When** a parent account has children, **Then** the parent displays an aggregated balance that is the sum of all its descendants' balances.
2. **Given** I am viewing the sidebar, **When** I first load the page, **Then** all parent accounts are collapsed by default, showing only root-level accounts with their aggregated totals.
3. **Given** a parent account is collapsed, **When** I click the expand icon (chevron), **Then** the child accounts are revealed below the parent with appropriate indentation.
4. **Given** a parent account is expanded, **When** I click the collapse icon, **Then** the child accounts are hidden and only the parent with aggregated total remains visible.
5. **Given** I have expanded some accounts, **When** I navigate away and return to the sidebar, **Then** my expand/collapse state is preserved (per session).
6. **Given** a 3-level hierarchy (grandparent > parent > child), **When** I view the grandparent collapsed, **Then** it shows the sum of all descendants (parent + grandchildren balances).
7. **Given** child balances change (e.g., new transaction), **When** I view the parent account, **Then** the aggregated balance is updated to reflect the new totals.

---

### User Story 7 - Switch Application Language (Priority: P3)

As a user, I want to switch between languages (zh-TW, en) in the Settings so I can use the application in my preferred language.

**Why this priority**: Enhances accessibility for different language users, but the application already has i18n support from 002 feature.

**Independent Test**: Can be fully tested by switching to a different language and verifying all UI text changes accordingly.

**Acceptance Scenarios**:

1. **Given** I am on the Settings page, **When** I select a different language from the language dropdown, **Then** all application text immediately changes to the selected language.
2. **Given** I have changed the language, **When** I close and reopen the application, **Then** my language preference is remembered.

---

### User Story 8 - Switch Between Dark and Light Mode (Priority: P3)

As a user, I want to switch between dark and light display modes so I can choose the visual theme that is most comfortable for my eyes.

**Why this priority**: Quality-of-life improvement that enhances user experience but is not essential for core functionality.

**Independent Test**: Can be fully tested by toggling the theme switch and verifying the application's visual appearance changes.

**Acceptance Scenarios**:

1. **Given** I am on the Settings page, **When** I toggle the theme switch, **Then** the application immediately switches between dark and light modes.
2. **Given** I have selected a theme, **When** I close and reopen the application, **Then** my theme preference is remembered.
3. **Given** I am using the application for the first time, **When** no theme preference is set, **Then** the application uses the system default theme preference.

---

### Edge Cases

- What happens when a user tries to delete an account that is referenced in transaction templates? (Transaction templates are out of scope for this feature; if implemented later, templates should also be updated during reassignment.)
- How does the system handle accounts with very long names in the sidebar display?
- What happens when drag-and-drop is used on mobile devices with touch interfaces?
- How does the system handle circular parent-child references (should be prevented)?
- What happens when language is changed while a form has unsaved data?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a Settings entry point in the sidebar menu.
- **FR-002**: System MUST provide an Account Management section within Settings.
- **FR-003**: Users MUST be able to create new accounts with a name and parent account selection.
- **FR-004**: System MUST support all four account types (Asset, Liability, Income, Expense) for new accounts.
- **FR-005**: System MUST enforce unique account names within the same parent.
- **FR-006**: Users MUST be able to edit existing account names.
- **FR-007**: System MUST update account names consistently across all views when edited.
- **FR-008**: Users MUST be able to delete accounts that have no associated transactions.
- **FR-009**: System MUST prompt user to select a replacement account when deleting an account with transactions, reassigning all transactions before deletion.
- **FR-009a**: Replacement account selection MUST only show accounts of the same type (e.g., Asset can only be replaced by another Asset account).
- **FR-010**: System MUST prevent deletion of parent accounts that have child accounts.
- **FR-011**: Users MUST be able to reorder accounts using drag-and-drop within the account management page.
- **FR-012**: System MUST persist account order and reflect it in the sidebar.
- **FR-013**: System MUST support up to 3 levels of account hierarchy.
- **FR-014**: System MUST prevent creation of accounts deeper than 3 levels.
- **FR-021**: Parent accounts in sidebar MUST display aggregated balances (sum of all descendant balances).
- **FR-022**: Parent accounts in sidebar MUST be collapsible/expandable via chevron icon.
- **FR-023**: Sidebar MUST default to collapsed state (only root accounts visible) on initial load.
- **FR-024**: Sidebar expand/collapse state MUST be preserved within the user's session.
- **FR-025**: Aggregated balances MUST be calculated recursively (grandparent includes parent + grandchildren).
- **FR-015**: Users MUST be able to switch the application language between zh-TW and en.
- **FR-016**: System MUST persist the user's language preference.
- **FR-017**: Users MUST be able to toggle between dark and light display modes.
- **FR-018**: System MUST persist the user's theme preference.
- **FR-019**: System MUST default to the operating system's theme preference when no user preference is set.
- **FR-020**: System MUST allow users to move accounts to different parents via drag-and-drop (within hierarchy depth limits).

### Data Integrity Requirements

- **DI-001**: System MUST validate account names are non-empty and within reasonable length limits (e.g., 1-100 characters).
- **DI-002**: System MUST maintain referential integrity - deleted accounts cannot leave orphaned references.
- **DI-003**: System MUST prevent circular parent-child relationships.
- **DI-004**: System MUST maintain audit trail for account creation, modification, and deletion (who, what, when).

### Key Entities

- **Account (科目)**: Represents a category for organizing transactions. Has a name, type (Asset/Liability/Income/Expense), optional parent account, and sort order.
- **User Preference**: Stores user-specific settings including language preference and theme selection. Persisted in browser local storage (per-device, no cross-device sync).
- **Account Hierarchy**: The tree structure of parent-child relationships between accounts, limited to 3 levels.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new account in under 30 seconds from Settings entry.
- **SC-002**: Users can reorganize their account structure (add, edit, delete, reorder) without needing external documentation.
- **SC-003**: 95% of account management operations complete successfully on first attempt.
- **SC-004**: Language and theme changes take effect immediately (within 1 second) with no page reload required.
- **SC-005**: Account hierarchy displays correctly with all 3 levels visible and distinguishable in both sidebar and account management views.
- **SC-006**: User preferences (language, theme) persist correctly across sessions 100% of the time.
- **SC-007**: Mobile users can access all account management features on devices with screen width 320px or larger.

## Assumptions

- The existing account model from 001-core-accounting will be extended to support parent-child relationships and sort order.
- The existing i18n infrastructure from 002-ui-layout-dashboard will be leveraged for language switching.
- MyAB format parsing (mentioned in roadmap: A-代墊應收帳款.借別人錢) will be handled in the data import feature (006), not in this feature.
- Theme switching will apply to the entire application, not individual pages.
- Maximum account name length of 100 characters is sufficient for all practical use cases.
- Drag-and-drop on mobile will use touch-and-hold gesture to initiate.

## Out of Scope

- MyAB CSV import/parsing (covered in 006-data-import)
- Batch account operations (bulk delete, bulk move)
- Account archiving (soft delete with visibility toggle)
- Account merging functionality
- Custom account icons or colors
- Account-level permissions/access control
