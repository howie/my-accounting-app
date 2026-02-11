"""Gmail API service for OAuth2 authentication and email operations.

Handles Gmail OAuth2 flow, token management, and email/attachment operations.
"""

import json
import os
import secrets
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from src.services.encryption import decrypt, encrypt

# OAuth2 scopes - read-only access to Gmail
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailServiceError(Exception):
    """Base exception for Gmail service errors."""

    pass


class GmailAuthError(GmailServiceError):
    """Error during OAuth2 authentication."""

    pass


class GmailApiError(GmailServiceError):
    """Error when calling Gmail API."""

    pass


class GmailService:
    """Service for Gmail OAuth2 and API operations.

    Handles:
    - OAuth2 authorization flow
    - Token storage and refresh
    - Email search and attachment download
    """

    def __init__(self) -> None:
        """Initialize Gmail service with credentials from environment."""
        self.client_id = os.environ.get("GOOGLE_CLIENT_ID")
        self.client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.environ.get(
            "GMAIL_OAUTH_REDIRECT_URI", "http://localhost:8000/api/v1/gmail/auth/callback"
        )

        if not self.client_id or not self.client_secret:
            raise GmailServiceError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment"
            )

    def get_auth_url(self, ledger_id: UUID) -> tuple[str, str]:
        """Generate OAuth2 authorization URL.

        Args:
            ledger_id: The ledger ID to associate with this connection.

        Returns:
            Tuple of (auth_url, state) where state is used for CSRF protection.
        """
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Encode ledger_id in state for retrieval after callback
        state_data = json.dumps({"state": state, "ledger_id": str(ledger_id)})
        encoded_state = secrets.token_urlsafe(16) + "." + state_data.replace('"', "'")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=SCOPES,
        )
        flow.redirect_uri = self.redirect_uri

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",  # Force consent to get refresh token
            state=encoded_state,
        )

        return auth_url, encoded_state

    def handle_callback(self, code: str, state: str) -> tuple[str, str, str, datetime | None, str]:
        """Handle OAuth2 callback and exchange code for tokens.

        Args:
            code: Authorization code from Google.
            state: State parameter for CSRF validation.

        Returns:
            Tuple of (encrypted_access_token, encrypted_refresh_token,
                     email_address, token_expiry, ledger_id)

        Raises:
            GmailAuthError: If callback validation or token exchange fails.
        """
        try:
            # Parse state to get ledger_id
            state_parts = state.split(".", 1)
            if len(state_parts) != 2:
                raise GmailAuthError("Invalid state format")

            state_data = json.loads(state_parts[1].replace("'", '"'))
            ledger_id = state_data.get("ledger_id")

            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri],
                    }
                },
                scopes=SCOPES,
            )
            flow.redirect_uri = self.redirect_uri

            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials

            if not credentials.refresh_token:
                raise GmailAuthError(
                    "No refresh token received. User may need to revoke access and try again."
                )

            # Get user's email address
            service = build("gmail", "v1", credentials=credentials)
            profile = service.users().getProfile(userId="me").execute()
            email_address = profile.get("emailAddress", "")

            # Encrypt tokens for storage
            encrypted_access = encrypt(credentials.token)
            encrypted_refresh = encrypt(credentials.refresh_token)

            return (
                encrypted_access,
                encrypted_refresh,
                email_address,
                credentials.expiry,
                ledger_id,
            )

        except json.JSONDecodeError as e:
            raise GmailAuthError(f"Invalid state parameter: {e}") from e
        except Exception as e:
            if isinstance(e, GmailAuthError):
                raise
            raise GmailAuthError(f"OAuth2 callback failed: {e}") from e

    def get_credentials(
        self,
        encrypted_access_token: str,
        encrypted_refresh_token: str,
        token_expiry: datetime | None,
    ) -> Credentials:
        """Create Credentials object from encrypted tokens.

        Args:
            encrypted_access_token: Fernet-encrypted access token.
            encrypted_refresh_token: Fernet-encrypted refresh token.
            token_expiry: Token expiration datetime.

        Returns:
            Google OAuth2 Credentials object.
        """
        access_token = decrypt(encrypted_access_token)
        refresh_token = decrypt(encrypted_refresh_token)

        return Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            expiry=token_expiry,
        )

    def refresh_credentials(self, credentials: Credentials) -> tuple[str, str, datetime | None]:
        """Refresh expired credentials.

        Args:
            credentials: Credentials object to refresh.

        Returns:
            Tuple of (encrypted_access_token, encrypted_refresh_token, new_expiry).

        Raises:
            GmailAuthError: If refresh fails.
        """
        try:
            credentials.refresh(Request())

            encrypted_access = encrypt(credentials.token)
            encrypted_refresh = encrypt(
                credentials.refresh_token if credentials.refresh_token else ""
            )

            return encrypted_access, encrypted_refresh, credentials.expiry

        except Exception as e:
            raise GmailAuthError(f"Token refresh failed: {e}") from e

    def get_gmail_service(self, credentials: Credentials) -> Any:
        """Get authenticated Gmail API service.

        Args:
            credentials: Valid OAuth2 credentials.

        Returns:
            Gmail API service object.
        """
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        return build("gmail", "v1", credentials=credentials)

    def search_messages(self, service: Any, query: str, max_results: int = 100) -> list[dict]:
        """Search Gmail for messages matching query.

        Args:
            service: Authenticated Gmail API service.
            query: Gmail search query (e.g., "from:bank.com has:attachment").
            max_results: Maximum number of messages to return.

        Returns:
            List of message metadata dicts with 'id' and 'threadId'.
        """
        try:
            messages = []
            request = service.users().messages().list(userId="me", q=query, maxResults=max_results)

            while request:
                response = request.execute()
                messages.extend(response.get("messages", []))

                if len(messages) >= max_results:
                    break

                request = service.users().messages().list_next(request, response)

            return messages[:max_results]

        except Exception as e:
            raise GmailApiError(f"Failed to search messages: {e}") from e

    def get_message(self, service: Any, message_id: str) -> dict:
        """Get full message details including headers and parts.

        Args:
            service: Authenticated Gmail API service.
            message_id: Gmail message ID.

        Returns:
            Full message object.
        """
        try:
            return service.users().messages().get(userId="me", id=message_id).execute()
        except Exception as e:
            raise GmailApiError(f"Failed to get message {message_id}: {e}") from e

    def get_attachment(self, service: Any, message_id: str, attachment_id: str) -> bytes:
        """Download an attachment from a message.

        Args:
            service: Authenticated Gmail API service.
            message_id: Gmail message ID.
            attachment_id: Attachment ID within the message.

        Returns:
            Raw attachment bytes.
        """
        import base64

        try:
            attachment = (
                service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=message_id, id=attachment_id)
                .execute()
            )

            # Decode base64url encoded data
            data = attachment.get("data", "")
            return base64.urlsafe_b64decode(data)

        except Exception as e:
            raise GmailApiError(f"Failed to get attachment: {e}") from e

    def extract_pdf_attachments(self, message: dict) -> list[dict]:
        """Extract PDF attachment info from a message.

        Args:
            message: Full Gmail message object.

        Returns:
            List of dicts with 'attachment_id', 'filename', 'size'.
        """
        attachments = []

        def process_parts(parts: list) -> None:
            for part in parts:
                if part.get("parts"):
                    process_parts(part["parts"])

                filename = part.get("filename", "")
                if filename.lower().endswith(".pdf"):
                    body = part.get("body", {})
                    if "attachmentId" in body:
                        attachments.append(
                            {
                                "attachment_id": body["attachmentId"],
                                "filename": filename,
                                "size": body.get("size", 0),
                            }
                        )

        payload = message.get("payload", {})
        if payload.get("parts"):
            process_parts(payload["parts"])
        elif payload.get("filename", "").lower().endswith(".pdf"):
            body = payload.get("body", {})
            if "attachmentId" in body:
                attachments.append(
                    {
                        "attachment_id": body["attachmentId"],
                        "filename": payload["filename"],
                        "size": body.get("size", 0),
                    }
                )

        return attachments

    def extract_message_metadata(self, message: dict) -> dict:
        """Extract useful metadata from a message.

        Args:
            message: Full Gmail message object.

        Returns:
            Dict with 'subject', 'from', 'date', 'message_id'.
        """
        headers = message.get("payload", {}).get("headers", [])
        header_dict = {h["name"].lower(): h["value"] for h in headers}

        # Parse internal date (milliseconds since epoch)
        internal_date_ms = int(message.get("internalDate", 0))
        date = datetime.fromtimestamp(internal_date_ms / 1000, tz=UTC) if internal_date_ms else None

        return {
            "subject": header_dict.get("subject", ""),
            "from": header_dict.get("from", ""),
            "date": date,
            "message_id": message.get("id", ""),
        }

    def revoke_credentials(self, credentials: Credentials) -> bool:
        """Revoke OAuth2 credentials.

        Args:
            credentials: Credentials to revoke.

        Returns:
            True if revocation succeeded.
        """
        import requests

        try:
            requests.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": credentials.token},
                headers={"content-type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            return True
        except Exception:
            # Revocation failure is not critical
            return False
