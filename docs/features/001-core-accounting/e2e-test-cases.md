# E2E Test Cases: Core Accounting System

## Test Case Format

Each test case includes:

- **ID**: Unique identifier (TC-XXX-NNN)
- **Priority**: P0/P1/P2/P3
- **Preconditions**: Required state before test
- **Steps**: Actions to perform
- **Expected Results**: What should happen

---

## 1. User Setup (TC-USR-xxx)

### TC-USR-001: New User Setup

**Priority**: P0

**Preconditions**:

- Clean database
- Application accessible at localhost:3000

**Steps**:

1. Navigate to homepage
2. Click "Get Started" or similar CTA
3. Enter email address: `test-user@example.com`
4. Submit the form

**Expected Results**:

- User is created in database
- User is redirected to ledger list page
- Session is established (user remains logged in on refresh)

### TC-USR-002: Existing User Return

**Priority**: P1

**Preconditions**:

- User `test-user@example.com` exists with ledgers

**Steps**:

1. Navigate to homepage
2. Enter existing email: `test-user@example.com`
3. Submit the form

**Expected Results**:

- User is recognized (not duplicated)
- User sees their existing ledgers

### TC-USR-003: User Data Isolation

**Priority**: P0

**Preconditions**:

- User A has ledger "Personal"
- User B has ledger "Business"

**Steps**:

1. Log in as User A
2. View ledger list

**Expected Results**:

- User A sees only "Personal" ledger
- User A cannot access User B's "Business" ledger via URL manipulation

---

## 2. Ledger Management (TC-LDG-xxx)

### TC-LDG-001: Create Ledger with Initial Balance

**Priority**: P0

**Preconditions**:

- User is logged in
- On ledger list page

**Steps**:

1. Click "Create New Ledger"
2. Enter name: "My Personal Finance"
3. Enter initial balance: 1000.00
4. Submit form

**Expected Results**:

- Ledger created with name "My Personal Finance"
- Initial balance shown as $1,000.00
- System accounts created: Cash (ASSET), Equity (LIABILITY)
- Cash account balance = initial balance
- User redirected to ledger detail page

### TC-LDG-002: Create Ledger with Zero Balance

**Priority**: P1

**Preconditions**:

- User is logged in

**Steps**:

1. Create ledger with name "Empty Ledger"
2. Leave initial balance as 0 or empty

**Expected Results**:

- Ledger created successfully
- Cash account balance = $0.00

### TC-LDG-003: View Ledger List

**Priority**: P0

**Preconditions**:

- User has 3 ledgers

**Steps**:

1. Navigate to /ledgers

**Expected Results**:

- All 3 ledgers displayed
- Each shows name, initial balance, created date

### TC-LDG-004: View Ledger Details

**Priority**: P0

**Preconditions**:

- Ledger "Test Ledger" exists with accounts and transactions

**Steps**:

1. Click on "Test Ledger" from list

**Expected Results**:

- Ledger name displayed
- Initial balance shown
- Accounts section visible
- Transactions section visible

### TC-LDG-005: Delete Empty Ledger

**Priority**: P1

**Preconditions**:

- Ledger with only system accounts exists

**Steps**:

1. Go to ledger detail page
2. Click "Delete Ledger"
3. Confirm deletion

**Expected Results**:

- Ledger deleted
- Associated accounts deleted
- User redirected to ledger list

### TC-LDG-006: Delete Ledger with Transactions

**Priority**: P1

**Preconditions**:

- Ledger has accounts and transactions

**Steps**:

1. Delete the ledger
2. Confirm deletion

**Expected Results**:

- Ledger deleted
- All accounts deleted (cascade)
- All transactions deleted (cascade)

---

## 3. Account Management - Basic (TC-ACC-xxx)

### TC-ACC-001: Create Root EXPENSE Account

**Priority**: P0

**Preconditions**:

- On ledger detail page

**Steps**:

1. Click "New Account"
2. Enter name: "Food & Dining"
3. Select type: EXPENSE
4. Leave parent as "None (Root Level)"
5. Submit

**Expected Results**:

- Account created with depth=1
- Account appears in EXPENSE section
- Balance = $0.00

### TC-ACC-002: Create Root ASSET Account

**Priority**: P0

**Preconditions**:

- On ledger detail page

**Steps**:

1. Create account with name "Bank Account", type ASSET

**Expected Results**:

- Account created as root level ASSET
- Appears in ASSET section

### TC-ACC-003: Create Root INCOME Account

**Priority**: P0

**Preconditions**:

- On ledger detail page

**Steps**:

1. Create account with name "Salary", type INCOME

**Expected Results**:

- Account created as root level INCOME

### TC-ACC-004: Create Root LIABILITY Account

**Priority**: P0

**Preconditions**:

- On ledger detail page

**Steps**:

1. Create account with name "Credit Card", type LIABILITY

**Expected Results**:

- Account created as root level LIABILITY

### TC-ACC-005: Duplicate Account Name (Same Type)

**Priority**: P1

**Preconditions**:

- Account "Food" (EXPENSE) exists

**Steps**:

1. Try to create another EXPENSE account named "Food"

**Expected Results**:

- Error displayed: "Account with name 'Food' already exists"
- Account not created

### TC-ACC-006: Same Name Different Types

**Priority**: P2

**Preconditions**:

- Account "Misc" (EXPENSE) exists

**Steps**:

1. Create INCOME account named "Misc"

**Expected Results**:

- Account created successfully (different types allowed)

### TC-ACC-007: Delete Leaf Account (No Transactions)

**Priority**: P0

**Preconditions**:

- Account "Test Account" exists with no transactions

**Steps**:

1. Click Delete on "Test Account"
2. Confirm deletion

**Expected Results**:

- Account deleted
- Removed from account list

### TC-ACC-008: Delete System Account

**Priority**: P0

**Preconditions**:

- System account "Cash" exists

**Steps**:

1. Attempt to delete "Cash" account

**Expected Results**:

- Delete button not visible OR
- Error: "Cannot delete system account"

### TC-ACC-009: Delete Account with Transactions

**Priority**: P1

**Preconditions**:

- Account "Groceries" has transactions

**Steps**:

1. Attempt to delete "Groceries"

**Expected Results**:

- Error: "Cannot delete account with transactions"
- Account not deleted

---

## 4. Account Hierarchy (TC-HIR-xxx)

### TC-HIR-001: Create Child Account (Level 2)

**Priority**: P0

**Preconditions**:

- Root EXPENSE account "Living Expenses" exists (depth=1)

**Steps**:

1. Click "New Account"
2. Enter name: "Utilities"
3. Select type: EXPENSE
4. Select parent: "Living Expenses"
5. Submit

**Expected Results**:

- Account created with depth=2
- Account appears as child of "Living Expenses"
- Parent shows expand icon (▶)

### TC-HIR-002: Create Grandchild Account (Level 3)

**Priority**: P0

**Preconditions**:

- Root "Living Expenses" (depth=1)
- Child "Utilities" (depth=2)

**Steps**:

1. Create EXPENSE account "Electricity" under "Utilities"

**Expected Results**:

- Account created with depth=3
- Nested under Utilities in tree view

### TC-HIR-003: Attempt Level 4 (Max Depth Exceeded)

**Priority**: P0

**Preconditions**:

- Account at depth=3 exists ("Electricity")

**Steps**:

1. Try to create child under "Electricity"

**Expected Results**:

- Parent dropdown does not show depth=3 accounts OR
- Error: "Maximum depth exceeded"

### TC-HIR-004: Parent Type Mismatch

**Priority**: P0

**Preconditions**:

- EXPENSE account "Food" exists

**Steps**:

1. Try to create INCOME account with parent "Food"

**Expected Results**:

- "Food" not shown in parent dropdown (filtered by type) OR
- Error: "Child account must have same type as parent"

### TC-HIR-005: Expand/Collapse Tree

**Priority**: P1

**Preconditions**:

- Hierarchical accounts exist (parent with children)

**Steps**:

1. View account list
2. Click expand icon (▶) on parent account
3. Click collapse icon (▼) on same account

**Expected Results**:

- Children shown when expanded
- Children hidden when collapsed
- Icon toggles between ▶ and ▼

### TC-HIR-006: Delete Parent Account (Has Children)

**Priority**: P0

**Preconditions**:

- Parent "Living Expenses" has child "Utilities"

**Steps**:

1. Attempt to delete "Living Expenses"

**Expected Results**:

- Error: "Cannot delete account with child accounts"
- Account not deleted
- "(has children)" indicator visible

### TC-HIR-007: Balance Aggregation in Tree

**Priority**: P0

**Preconditions**:

- Parent "Food" (EXPENSE) with children:
  - "Groceries" balance $100
  - "Restaurants" balance $50

**Steps**:

1. View account tree

**Expected Results**:

- "Food" shows balance $150 (aggregated)
- "(total)" label displayed next to parent balance
- Children show individual balances

### TC-HIR-008: Transaction on Leaf Only

**Priority**: P0

**Preconditions**:

- Parent "Food" has child "Groceries"

**Steps**:

1. Create transaction with to_account = "Food" (parent)

**Expected Results**:

- Error: "Transactions can only be recorded on leaf accounts"
- "Food" should not appear in transaction form dropdown OR filtered

---

## 5. Transaction Management (TC-TXN-xxx)

### TC-TXN-001: Create EXPENSE Transaction

**Priority**: P0

**Preconditions**:

- Cash (ASSET) account exists with balance $1000
- Groceries (EXPENSE) account exists

**Steps**:

1. Click "New Transaction"
2. Enter date: today
3. Enter description: "Weekly groceries"
4. Enter amount: 50.00
5. Select type: EXPENSE
6. Select from: Cash
7. Select to: Groceries
8. Submit

**Expected Results**:

- Transaction created
- Cash balance reduced to $950
- Groceries balance increased to $50
- Transaction appears in list

### TC-TXN-002: Create INCOME Transaction

**Priority**: P0

**Preconditions**:

- Salary (INCOME) account exists
- Bank Account (ASSET) exists

**Steps**:

1. Create INCOME transaction
2. From: Salary, To: Bank Account
3. Amount: 3000.00

**Expected Results**:

- Bank Account balance increased by $3000
- Transaction type shows as INCOME

### TC-TXN-003: Create TRANSFER Transaction

**Priority**: P0

**Preconditions**:

- Cash (ASSET) and Bank Account (ASSET) exist

**Steps**:

1. Create TRANSFER transaction
2. From: Bank Account, To: Cash
3. Amount: 200.00

**Expected Results**:

- Bank Account balance reduced by $200
- Cash balance increased by $200

### TC-TXN-004: Invalid EXPENSE Accounts

**Priority**: P1

**Preconditions**:

- Salary (INCOME) and Groceries (EXPENSE) exist

**Steps**:

1. Try to create EXPENSE transaction
2. From: Salary (INCOME), To: Groceries

**Expected Results**:

- Error: "EXPENSE from_account must be Asset or Liability"

### TC-TXN-005: Same Account Transaction

**Priority**: P1

**Preconditions**:

- Any account exists

**Steps**:

1. Create transaction with same from and to account

**Expected Results**:

- Error: "Cannot create transaction with same account"

### TC-TXN-006: Update Transaction

**Priority**: P1

**Preconditions**:

- Transaction exists: $50 from Cash to Groceries

**Steps**:

1. Edit the transaction
2. Change amount to $75
3. Save

**Expected Results**:

- Transaction updated
- Cash balance adjusted (was -50, now -75)
- Groceries balance adjusted

### TC-TXN-007: Delete Transaction

**Priority**: P1

**Preconditions**:

- Transaction: $50 from Cash to Groceries

**Steps**:

1. Delete the transaction
2. Confirm

**Expected Results**:

- Transaction removed from list
- Cash balance restored (+$50)
- Groceries balance restored (-$50)

### TC-TXN-008: Transaction List Pagination

**Priority**: P2

**Preconditions**:

- 60 transactions exist (more than page size)

**Steps**:

1. View transaction list
2. Scroll to bottom / click "Load More"

**Expected Results**:

- First page shows ~50 transactions
- More transactions loaded on demand
- Ordered by date descending

### TC-TXN-009: Search Transactions

**Priority**: P2

**Preconditions**:

- Transactions with various descriptions exist

**Steps**:

1. Enter search term: "grocery"
2. Submit search

**Expected Results**:

- Only transactions with "grocery" in description shown
- Case-insensitive matching

### TC-TXN-010: Filter by Date Range

**Priority**: P2

**Preconditions**:

- Transactions from different dates exist

**Steps**:

1. Set From Date: 2024-01-01
2. Set To Date: 2024-01-31

**Expected Results**:

- Only January 2024 transactions shown

### TC-TXN-011: Filter by Account

**Priority**: P2

**Preconditions**:

- Transactions involving different accounts

**Steps**:

1. Select account filter: "Groceries"

**Expected Results**:

- Only transactions where Groceries is from_account OR to_account

### TC-TXN-012: Filter by Transaction Type

**Priority**: P2

**Preconditions**:

- Mix of EXPENSE, INCOME, TRANSFER transactions

**Steps**:

1. Select type filter: "EXPENSE"

**Expected Results**:

- Only EXPENSE transactions shown

---

## 6. Balance Display (TC-BAL-xxx)

### TC-BAL-001: Initial Cash Balance

**Priority**: P0

**Preconditions**:

- New ledger with initial balance $1000

**Steps**:

1. View Cash account balance

**Expected Results**:

- Cash shows $1,000.00

### TC-BAL-002: Balance After Expense

**Priority**: P0

**Preconditions**:

- Cash balance $1000
- Create $50 expense

**Steps**:

1. View Cash balance after transaction

**Expected Results**:

- Cash shows $950.00

### TC-BAL-003: Negative Balance Warning

**Priority**: P1

**Preconditions**:

- Account with $100 balance

**Steps**:

1. Create expense of $150

**Expected Results**:

- Balance shows -$50.00
- Warning icon (⚠️) displayed
- Balance text in red/destructive color

### TC-BAL-004: Parent Balance Updates

**Priority**: P1

**Preconditions**:

- Parent "Food" with child "Groceries"
- Transaction to "Groceries" for $30

**Steps**:

1. View account tree
2. Expand "Food"

**Expected Results**:

- Groceries shows $30
- Food shows $30 (aggregated)

---

## 7. Complete User Journeys (TC-JRN-xxx)

### TC-JRN-001: New User Full Setup

**Priority**: P0

**Preconditions**:

- Clean application state

**Steps**:

1. Register as new user
2. Create ledger "Personal Budget" with $5000
3. Create accounts:
   - Food (EXPENSE)
     - Groceries (child)
     - Restaurants (child)
   - Transportation (EXPENSE)
   - Salary (INCOME)
4. Record transactions:
   - Income: $3000 from Salary to Cash
   - Expense: $200 from Cash to Groceries
   - Expense: $50 from Cash to Restaurants
5. View account tree

**Expected Results**:

- All operations succeed
- Cash balance: $5000 + $3000 - $200 - $50 = $7750
- Food total: $250 (aggregated)
- Transaction list shows all 3 transactions

### TC-JRN-002: Monthly Expense Tracking

**Priority**: P1

**Preconditions**:

- Ledger with hierarchical expense accounts

**Steps**:

1. Record 10 different expense transactions across categories
2. Filter by current month
3. View category totals in tree

**Expected Results**:

- All expenses recorded correctly
- Tree shows aggregated totals per category
- Monthly filter shows correct subset

---

## Test Data Templates

### Standard Test Ledger

```json
{
  "name": "Test Ledger",
  "initial_balance": 10000.0,
  "accounts": [
    { "name": "Cash", "type": "ASSET", "is_system": true },
    { "name": "Equity", "type": "LIABILITY", "is_system": true },
    { "name": "Bank", "type": "ASSET" },
    {
      "name": "Living Expenses",
      "type": "EXPENSE",
      "children": [
        {
          "name": "Utilities",
          "children": [{ "name": "Electricity" }, { "name": "Water" }]
        },
        { "name": "Rent" }
      ]
    },
    { "name": "Salary", "type": "INCOME" }
  ]
}
```

### Transaction Test Data

```json
{
  "transactions": [
    {
      "type": "INCOME",
      "from": "Salary",
      "to": "Bank",
      "amount": 5000,
      "desc": "Monthly salary"
    },
    {
      "type": "TRANSFER",
      "from": "Bank",
      "to": "Cash",
      "amount": 500,
      "desc": "ATM withdrawal"
    },
    {
      "type": "EXPENSE",
      "from": "Cash",
      "to": "Electricity",
      "amount": 100,
      "desc": "Electric bill"
    }
  ]
}
```
