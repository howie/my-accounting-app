# API Token Management Contracts

**Feature**: 007-api-for-mcp
**Date**: 2026-01-11
**Protocol**: REST API (existing FastAPI)

## Overview

These endpoints allow users to manage their API tokens for MCP access through the web interface.

## Base URL

```
/api/v1/tokens
```

## Authentication

All endpoints require session authentication (existing web auth).

---

## Endpoints

### 1. List Tokens

Lists all API tokens for the authenticated user.

```
GET /api/v1/tokens
```

#### Response

```json
{
  "tokens": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Claude Desktop",
      "token_prefix": "ldo_abc1",
      "created_at": "2026-01-11T10:30:00Z",
      "last_used_at": "2026-01-11T14:22:00Z",
      "is_revoked": false
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "ChatGPT",
      "token_prefix": "ldo_def2",
      "created_at": "2026-01-10T09:00:00Z",
      "last_used_at": null,
      "is_revoked": false
    }
  ]
}
```

---

### 2. Create Token

Creates a new API token.

```
POST /api/v1/tokens
```

#### Request Body

```json
{
  "name": "Claude Desktop"
}
```

#### Validation

- `name`: Required, 1-100 characters

#### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Claude Desktop",
  "token": "ldo_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
  "token_prefix": "ldo_abc1",
  "created_at": "2026-01-11T10:30:00Z",
  "message": "Token created. Copy it now - it won't be shown again."
}
```

**Important**: The full `token` is only returned once at creation time. Store it securely.

---

### 3. Revoke Token

Revokes an API token (soft delete).

```
DELETE /api/v1/tokens/{token_id}
```

#### Path Parameters

- `token_id`: UUID of the token to revoke

#### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Claude Desktop",
  "revoked_at": "2026-01-11T15:00:00Z",
  "message": "Token revoked successfully"
}
```

#### Error Response (404 Not Found)

```json
{
  "error": {
    "code": "TOKEN_NOT_FOUND",
    "message": "Token not found or already revoked"
  }
}
```

---

## Token Format

Tokens follow this format:

```
ldo_<48 random alphanumeric characters>
```

- Prefix: `ldo_` (LedgerOne)
- Body: 48 characters from `[a-zA-Z0-9]`
- Total length: 52 characters
- Example: `ldo_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz`

### Storage

- Only the SHA-256 hash of the token is stored in the database
- The prefix (`ldo_abc1`) is stored separately for display purposes
- Full token is shown only once at creation time

---

## Error Codes

| Code                   | HTTP Status | Description                                     |
| ---------------------- | ----------- | ----------------------------------------------- |
| `UNAUTHORIZED`         | 401         | Not logged in                                   |
| `TOKEN_NOT_FOUND`      | 404         | Token does not exist or belongs to another user |
| `VALIDATION_ERROR`     | 400         | Invalid request body                            |
| `TOKEN_LIMIT_EXCEEDED` | 400         | Maximum tokens per user reached (default: 10)   |
