# Service Contract: UserAccountService

**Responsibility**: Manage user authentication and account lifecycle.

## Methods

### `create_user`
Creates a new user account.

- **Input**:
  - `username`: string (alphanumeric)
  - `password`: string (alphanumeric)
- **Output**:
  - `user_id`: int
- **Errors**:
  - `DuplicateUsernameError`: If username exists.
  - `ValidationError`: If username/password invalid format.

### `authenticate_user`
Verifies credentials.

- **Input**:
  - `username`: string
  - `password`: string
- **Output**:
  - `user`: UserAccount (object or dict) or None if failed.

### `list_users`
Lists all user accounts (admin/debug only).

- **Input**: None
- **Output**: List[UserAccount]
