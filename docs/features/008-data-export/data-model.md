# Data Model: Data Export

## Export Schemas

### 1. CSV Transaction Export

Represents a single row in the exported CSV file. Strictly typed to ensure compatibility with Import Service (Feature 006).

| Field             | Type   | Description                                | Example                |
| ----------------- | ------ | ------------------------------------------ | ---------------------- |
| `Date`            | string | Transaction date (YYYY-MM-DD)              | "2024-01-01"           |
| `Type`            | string | Localized transaction type                 | "支出", "收入", "轉帳" |
| `Expense Account` | string | Name of Expense account (if Type=支出)     | "Food"                 |
| `Income Account`  | string | Name of Income account (if Type=收入)      | "Salary"               |
| `From Account`    | string | Source account name (Asset/Liability)      | "Cash"                 |
| `To Account`      | string | Destination account name (Asset/Liability) | "Bank"                 |
| `Amount`          | number | Transaction amount (positive)              | 500.00                 |
| `Description`     | string | Description/Note                           | "Lunch"                |
| `Invoice No`      | string | Optional invoice number                    | "INV-001"              |

### 2. HTML Export Structure

Represents the data structure passed to the Jinja2 template.

```python
class HtmlExportContext:
    generated_at: datetime
    date_range: str  # "2024-01-01 to 2024-01-31" or "All Time"
    account_filter: str | None  # "Cash Account" or None
    transactions: List[TransactionView]

class TransactionView:
    date: str
    type_label: str  # "Expense", "Income", etc.
    source_label: str # "Cash"
    target_label: str # "Food"
    amount: str      # Formatted currency "$500.00"
    description: str
```

## Validation Rules (Pre-Export)

These rules are enforced by the `ExportService` before generating the stream.

1. **Date Range**: `start_date` must be less than or equal to `end_date` (if both provided).
2. **Account Access**: User must own the `account_id` if specified (Multi-tenancy check).
3. **Format**: Must be one of `['csv', 'html']`.
