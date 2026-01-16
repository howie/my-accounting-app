# Export API Contract

## Overview

Provides endpoints to export financial data in various formats.

## Endpoints

### GET /api/v1/export/transactions

Downloads a file containing transactions filtered by the given parameters.

**Request**

| Parameter    | Type   | Required | Description                                           |
| ------------ | ------ | -------- | ----------------------------------------------------- |
| `start_date` | date   | No       | ISO 8601 (YYYY-MM-DD). If omitted, includes earliest. |
| `end_date`   | date   | No       | ISO 8601 (YYYY-MM-DD). If omitted, includes latest.   |
| `account_id` | uuid   | No       | Filter by specific account ID.                        |
| `format`     | string | Yes      | Export format: `csv` or `html`.                       |

**Response (Success - CSV)**

- **Status**: 200 OK
- **Headers**:
  - `Content-Type`: `text/csv; charset=utf-8`
  - `Content-Disposition`: `attachment; filename="export_{YYYYMMDD}.csv"`
- **Body**: Streaming text response (UTF-8 BOM + CSV content).

**Response (Success - HTML)**

- **Status**: 200 OK
- **Headers**:
  - `Content-Type`: `text/html; charset=utf-8`
  - `Content-Disposition`: `attachment; filename="export_{YYYYMMDD}.html"`
- **Body**: HTML document string.

**Response (Errors)**

- **422 Validation Error**:
  - Invalid date format.
  - `start_date` > `end_date`.
  - Unsupported `format`.
- **404 Not Found**:
  - `account_id` does not exist.
- **403 Forbidden**:
  - Accessing `account_id` belonging to another user.

## Test Scenarios

### Contract Tests

1. **Valid CSV Export**: Request with valid params returns 200 and CSV content-type.
2. **Valid HTML Export**: Request with `format=html` returns 200 and HTML content-type.
3. **Invalid Format**: Request with `format=pdf` returns 422.
4. **Invalid Date Range**: Request with start > end returns 422.

### Integration Tests

1. **Content Verification**: Export specific transactions -> Parse result -> Assert rows match DB.
2. **Filtering**:
   - Export with `account_id` -> Assert only transactions for that account are present.
   - Export with date range -> Assert transactions outside range are excluded.
3. **Empty State**: Export with no transactions -> Returns Header row only.
