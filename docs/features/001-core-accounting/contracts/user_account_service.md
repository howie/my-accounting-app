# API Contract: User Service

**Date**: 2026-01-02 (Updated from 2025-11-22)
**Feature**: Core Accounting System
**Base Path**: `/api/v1/users`

## Overview

This service manages user accounts. For the MVP, authentication is simplified (single-user assumption). Full authentication is deferred to a future feature.

## MVP Scope

For the core accounting feature, user management is minimal:

- Single default user created on first run
- No password authentication (local/self-hosted deployment)
- User context passed via header or session for API calls

Full authentication (login, registration, password management, OAuth) will be implemented in a separate feature.

## Endpoints

### GET /api/v1/users/me

Get the current user (default user for MVP).

**Response** (200 OK):

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@localhost",
  "created_at": "2026-01-01T00:00:00Z"
}
```

**Notes**:

- In MVP, always returns the default user
- In future, requires authentication token

---

### POST /api/v1/users/setup

Initial setup endpoint (MVP only).

**Request**:

```json
{
  "email": "user@example.com"
}
```

**Response** (201 Created):

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "created_at": "2026-01-02T10:00:00Z"
}
```

**Errors**:

- `409 Conflict`: User already exists (single-user mode)

**Notes**:

- Only callable once in MVP mode
- Creates the default user for the installation

---

## Data Transfer Objects

### UserRead

```python
class UserRead(SQLModel):
    id: uuid.UUID
    email: str
    created_at: datetime
```

### UserSetup

```python
class UserSetup(SQLModel):
    email: str = Field(max_length=255)
```

---

## Service Interface

```python
class UserService:
    async def get_current_user(self) -> User | None:
        """
        Get the current user.
        In MVP, returns the single default user.
        """
        ...

    async def setup_user(self, data: UserSetup) -> User:
        """
        Create the initial user (MVP).
        Raises ValueError if user already exists.
        """
        ...

    async def get_or_create_default_user(self) -> User:
        """
        Get the default user, creating if needed.
        Used for initial application setup.
        """
        ...
```

---

## Future Authentication Features

The following will be implemented in a dedicated auth feature:

- **POST /api/v1/auth/register** - User registration
- **POST /api/v1/auth/login** - Login with email/password
- **POST /api/v1/auth/logout** - Logout
- **POST /api/v1/auth/refresh** - Refresh access token
- **POST /api/v1/auth/forgot-password** - Password reset request
- **POST /api/v1/auth/reset-password** - Password reset confirmation
- **OAuth integrations** - Google, Apple sign-in

---

## MVP Authentication Flow

```
┌─────────────────────────────────────────────────────────┐
│                    MVP Flow                              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. App Start                                            │
│     └── Check if user exists                             │
│         ├── No  → Show setup screen                      │
│         │        └── POST /users/setup                   │
│         └── Yes → Load user context                      │
│                                                          │
│  2. All API Requests                                     │
│     └── User ID from session/context (no auth header)    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

This simplified flow allows development of core accounting features without the complexity of full authentication, which will be added later.
