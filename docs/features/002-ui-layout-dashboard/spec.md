# Feature Specification: UI Layout Improvement with Sidebar Navigation and Dashboard

**Feature Branch**: `002-ui-layout-dashboard`
**Created**: 2026-01-06
**Status**: Draft
**Input**: User description: "參考 MyAB 的 layout 把 Asset, loan, income, expense 都放在左側menu 然後點進去一個科目，右邊才會列出transaction 內容。另外首頁是 dashboard 顯示總資產，每月花費狀況，每月收入狀況"

## Clarifications

### Session 2026-01-06

- Q: Dashboard metrics display format? → A: Mirauve-style dashboard (reference: Dribbble shot 23051720) with card-based layout, large balance display, donut chart for income/expense breakdown, and bar charts for monthly trends.

## Overview

This feature redesigns the application's user interface to provide a more intuitive navigation experience. The new layout introduces a persistent left sidebar for navigating account categories (Assets, Loans, Income, Expenses), with a main content area that displays transactions when an account is selected. A dashboard homepage provides users with an at-a-glance view of their financial status including total assets, monthly expenses, and monthly income.

### Design Reference

The dashboard follows the Mirauve Financial Management Dashboard style (Dribbble shot 23051720):
- **Dark sidebar** with branding and navigation menu
- **Card-based main content** with rounded corners and subtle shadows
- **Balance overview card** displaying total assets prominently with large typography
- **Donut/pie chart** showing income vs expense breakdown for the current month
- **Bar charts** for monthly trends (income and expenses over 6 months)
- **Clean color scheme**: Dark sidebar, light content area, green for income/positive, purple/pink for expenses

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Financial Dashboard (Priority: P1)

As a user, I want to see my financial overview on the homepage so I can quickly understand my current financial situation without navigating through multiple screens.

**Why this priority**: The dashboard is the homepage and entry point for all users. It provides immediate value by showing key financial metrics at a glance, enabling users to make informed financial decisions quickly.

**Independent Test**: Can be fully tested by logging in and viewing the dashboard page. Delivers value by showing total assets, monthly expenses, and monthly income summaries.

**Acceptance Scenarios**:

1. **Given** the user is logged in, **When** they navigate to the homepage, **Then** they see a dashboard displaying total assets value
2. **Given** the user is logged in, **When** they view the dashboard, **Then** they see a summary of current month's expenses
3. **Given** the user is logged in, **When** they view the dashboard, **Then** they see a summary of current month's income
4. **Given** the user has no transactions, **When** they view the dashboard, **Then** they see zero values with appropriate messaging

---

### User Story 2 - Navigate Account Categories via Sidebar (Priority: P2)

As a user, I want to see all account categories (Assets, Loans, Income, Expenses) in a left sidebar menu so I can quickly navigate to any category without leaving the current view.

**Why this priority**: The sidebar navigation is the primary mechanism for accessing account data. Without this, users cannot browse their accounts in the new layout, making it essential for the feature to function.

**Independent Test**: Can be fully tested by clicking on sidebar menu items and verifying navigation works correctly. Delivers value by providing quick access to all account categories.

**Acceptance Scenarios**:

1. **Given** the user is on any page, **When** they view the left sidebar, **Then** they see menu items for Assets, Loans, Income, and Expenses
2. **Given** the sidebar is visible, **When** the user clicks on an account category, **Then** the category expands to show individual accounts within it
3. **Given** a category is expanded, **When** the user clicks on the category again, **Then** it collapses to hide individual accounts
4. **Given** the user is on mobile screen size, **When** they access the application, **Then** the sidebar is collapsible/expandable via a menu button

---

### User Story 3 - View Account Transactions (Priority: P2)

As a user, I want to click on a specific account in the sidebar and see its transactions displayed in the main content area so I can review account activity without losing my navigation context.

**Why this priority**: Viewing transactions is a core function of an accounting application. This story delivers the primary use case of accessing financial records while maintaining the new navigation paradigm.

**Independent Test**: Can be fully tested by selecting an account from the sidebar and verifying transactions appear in the main area. Delivers value by allowing users to review transaction history.

**Acceptance Scenarios**:

1. **Given** the user has expanded an account category, **When** they click on a specific account, **Then** the right side main area displays transactions for that account
2. **Given** transactions are displayed, **When** the user views the transaction list, **Then** each transaction shows date, description, and amount
3. **Given** an account has no transactions, **When** the user selects it, **Then** they see an empty state message indicating no transactions exist
4. **Given** an account has many transactions, **When** the user views the list, **Then** transactions are paginated or scrollable for performance

---

### User Story 4 - View Monthly Financial Trends (Priority: P3)

As a user, I want to see monthly expense and income trends on the dashboard so I can understand how my spending and earning patterns change over time.

**Why this priority**: While the basic dashboard shows current month data, trend visualization provides deeper insight. This is an enhancement that improves user experience but is not essential for core functionality.

**Independent Test**: Can be fully tested by viewing the dashboard and verifying trend visualizations display correctly with historical data. Delivers value by showing spending/income patterns over time.

**Acceptance Scenarios**:

1. **Given** the user is on the dashboard, **When** they view expense summary, **Then** they see a visual representation of monthly expense trends (last 6 months)
2. **Given** the user is on the dashboard, **When** they view income summary, **Then** they see a visual representation of monthly income trends (last 6 months)
3. **Given** the user has less than 6 months of data, **When** they view trends, **Then** only available months are displayed

---

### Edge Cases

- What happens when the user has no accounts created? Display appropriate onboarding message suggesting to create accounts first
- What happens when network connectivity is lost? Show cached data with offline indicator, prevent data modification
- How does the system handle very long account names? Truncate with ellipsis and show full name on hover/tooltip
- What happens when a user has hundreds of accounts in a single category? Enable scrolling within the category expansion in the sidebar
- How does the layout behave on different screen sizes? Responsive design with collapsible sidebar on mobile

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a persistent left sidebar navigation menu on all pages except full-screen modals
- **FR-002**: Sidebar MUST contain expandable/collapsible menu items for: Assets, Loans, Income, Expenses
- **FR-003**: Each category in the sidebar MUST expand to show individual accounts within that category
- **FR-004**: System MUST highlight the currently selected account in the sidebar
- **FR-005**: Main content area MUST display transaction list when an account is selected from sidebar
- **FR-006**: Transaction list MUST show date, description, and amount for each transaction
- **FR-007**: Dashboard homepage MUST display total assets value in a prominent balance overview card with large typography
- **FR-008**: Dashboard MUST display current month's total expenses in the income/expense summary
- **FR-009**: Dashboard MUST display current month's total income in the income/expense summary
- **FR-010**: Dashboard MUST display a donut chart showing income vs expense breakdown for the current month
- **FR-011**: Dashboard MUST display bar charts showing expense and income trends for the last 6 months
- **FR-012**: Sidebar MUST be collapsible on smaller screen sizes with a toggle button
- **FR-013**: System MUST preserve sidebar expanded/collapsed state during the user session
- **FR-014**: Transaction list MUST support pagination or infinite scroll for accounts with many transactions

### Data Integrity Requirements

*N/A - This feature focuses on UI layout and data display. It does not create, modify, or delete financial transactions. All displayed values are read-only views of existing data.*

### Key Entities

- **Account Category**: Groups accounts by type (Asset, Loan, Income, Expense). Used for sidebar organization.
- **Account**: Individual financial account belonging to a category. Displays in sidebar under its category, selection triggers transaction display.
- **Transaction**: Financial record associated with an account. Displayed in main content area with date, description, amount.
- **Dashboard Summary**: Aggregated financial metrics including total assets, monthly expenses, monthly income, and trend data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can navigate from dashboard to any account's transactions in 3 clicks or fewer
- **SC-002**: Dashboard page loads and displays all summary metrics within 2 seconds
- **SC-003**: Transaction list for an account loads within 1 second of selection
- **SC-004**: 90% of users can locate and select a specific account within 10 seconds on first use
- **SC-005**: Sidebar navigation is accessible and usable on screen widths from 320px to 2560px
- **SC-006**: Users can complete the task "check this month's total expenses" within 5 seconds of login

## Assumptions

- The existing account and transaction data structures support the required grouping by category
- Account categories (Asset, Loan, Income, Expense) are predefined and not user-customizable in this feature
- Dashboard calculations (totals, trends) are performed based on existing transaction data
- User session state management exists for storing UI preferences like sidebar state
- The application already has responsive design foundations that can be extended
- Currency formatting follows existing application standards
- Date/time formatting follows existing application standards
