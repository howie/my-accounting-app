# Research: Data Export Implementation

## Decisions

### 1. CSV Generation Strategy

- **Decision**: Use Python's standard `csv` library with `StreamingResponse`.
- **Rationale**:
  - `csv` library is robust, handles escaping automatically, and is standard in Python.
  - Streaming is required to support the 30,000 transaction limit defined in the Constitution without memory exhaustion.
  - Using `pandas` would be overkill and introduce a heavy dependency just for CSV writing.
- **Implementation**:
  - Create a generator function that yields strings (CSV lines).
  - Use `io.StringIO` to buffer individual lines for the CSV writer.

### 2. Character Encoding for Excel Compatibility

- **Decision**: UTF-8 with BOM (`\ufeff`).
- **Rationale**: Excel on Windows often misinterprets standard UTF-8 CSVs as ANSI, mangling non-ASCII characters (like Chinese "支出/收入"). Adding the Byte Order Mark (BOM) forces Excel to recognize the file as UTF-8.
- **Alternative**: UTF-16LE with tab separator (common in older systems), but UTF-8 w/ BOM is more universal for web use.

### 3. HTML Generation

- **Decision**: Jinja2 Templates.
- **Rationale**: FastAPI includes Jinja2 support. It separates the view logic (HTML structure) from the data logic.
- **Styling**: Inline CSS or a small `<style>` block in the head to ensure the file is self-contained (single file export).

### 4. Data Mapping for Import Compatibility

- **Decision**: Strict adherence to Feature 006 Import Service logic.
- **Mapping Table**:

| Transaction Type | CSV "Type" | CSV "Expense Account" | CSV "Income Account" | CSV "From Account"  | CSV "To Account"  |
| ---------------- | ---------- | --------------------- | -------------------- | ------------------- | ----------------- |
| Expense          | 支出       | `to_account` name     | (empty)              | `from_account` name | (empty)           |
| Income           | 收入       | (empty)               | `from_account` name  | (empty)             | `to_account` name |
| Transfer         | 轉帳       | (empty)               | (empty)              | `from_account` name | `to_account` name |

_Note: In the MyAB model:_

- _Expense_: Money moves FROM Asset TO Expense. (So `from`=Asset, `to`=Expense). The Import format expects "Expense Account" column to be the Expense category name.
- _Income_: Money moves FROM Income TO Asset. (So `from`=Income, `to`=Asset). The Import format expects "Income Account" column to be the Income category name.
- _Transfer_: Money moves FROM Asset TO Asset.

## Unknowns Resolved

- **Unknown**: Limit for export rows?
- **Resolution**: 30,000 (System Constraint). Streaming handles this.

- **Unknown**: Single Account Export context?
- **Resolution**: Exporting a single account should still produce the standard CSV format. If a transaction is "Expense: Food ($100) from Cash", and we export "Cash", we still show "Food" in the Expense Account column. The filter applies to the _selection_ of rows, not the _hiding of columns_.

## Checklist for Implementation

- [ ] Ensure `\ufeff` is yielded first in the stream.
- [ ] Ensure dates are formatted `YYYY/MM/DD` (or `YYYY-MM-DD` - check Import Service parser). _Import Service typically handles ISO, but Spec 5.2 example shows `2024/01/01`. We will use ISO `YYYY-MM-DD` as it is less ambiguous, or match the user locale if critical. Let's stick to YYYY-MM-DD for machine readability._
- [ ] Verify Chinese characters render correctly in Excel.
