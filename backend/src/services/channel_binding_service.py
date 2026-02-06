"""Channel binding service for OTP-based channel verification.

Handles code generation, verification, binding lifecycle, and lookups.
Based on 012-ai-multi-channel feature spec.
"""

import secrets
import uuid
from datetime import UTC, datetime

from sqlmodel import Session, select

from src.models.channel_binding import ChannelBinding, ChannelType

# OTP settings
CODE_LENGTH = 6
CODE_TTL_SECONDS = 300  # 5 minutes


class ChannelBindingService:
    """Manages channel binding lifecycle via OTP verification."""

    def __init__(self, session: Session) -> None:
        self.session = session
        # In-memory OTP store: code -> {user_id, channel_type, default_ledger_id, expires_at}
        # For production, this should be Redis-backed.
        if not hasattr(ChannelBindingService, "_otp_store"):
            ChannelBindingService._otp_store: dict[str, dict] = {}

    def generate_code(
        self,
        user_id: uuid.UUID,
        channel_type: ChannelType,
        default_ledger_id: uuid.UUID | None = None,
    ) -> str:
        """Generate a 6-digit OTP for channel binding.

        Returns the code string. Code expires after CODE_TTL_SECONDS.
        """
        code = self._make_unique_code()
        ChannelBindingService._otp_store[code] = {
            "user_id": user_id,
            "channel_type": channel_type,
            "default_ledger_id": default_ledger_id,
            "expires_at": datetime.now(UTC).timestamp() + CODE_TTL_SECONDS,
        }
        return code

    def verify_code(
        self,
        code: str,
        external_user_id: str,
        display_name: str | None = None,
    ) -> ChannelBinding | None:
        """Verify an OTP code and create a channel binding.

        Returns the ChannelBinding if valid, None if code is invalid/expired/consumed.
        Also returns None if the external_user_id already has an active binding
        for the same channel type (duplicate rejection).
        """
        entry = ChannelBindingService._otp_store.get(code)
        if entry is None:
            return None

        # Check expiry
        if datetime.now(UTC).timestamp() > entry["expires_at"]:
            del ChannelBindingService._otp_store[code]
            return None

        # Consume the code (one-time use)
        del ChannelBindingService._otp_store[code]

        channel_type = entry["channel_type"]
        user_id = entry["user_id"]
        default_ledger_id = entry["default_ledger_id"]

        # Check for duplicate active binding on same channel+external_user
        existing = self._find_active_binding(channel_type, external_user_id)
        if existing is not None:
            return None

        binding = ChannelBinding(
            user_id=user_id,
            channel_type=channel_type,
            external_user_id=external_user_id,
            display_name=display_name,
            default_ledger_id=default_ledger_id,
            is_active=True,
        )
        self.session.add(binding)
        self.session.commit()
        self.session.refresh(binding)
        return binding

    def list_bindings(
        self,
        user_id: uuid.UUID,
        include_inactive: bool = False,
    ) -> list[ChannelBinding]:
        """List bindings for a user. Active only by default."""
        statement = select(ChannelBinding).where(ChannelBinding.user_id == user_id)
        if not include_inactive:
            statement = statement.where(ChannelBinding.is_active.is_(True))
        statement = statement.order_by(ChannelBinding.created_at.desc())
        return list(self.session.exec(statement).all())

    def unbind(self, binding_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Soft-delete a binding (set is_active=False, record unbound_at).

        Returns True if unbound, False if not found or not owned by user.
        """
        statement = select(ChannelBinding).where(
            ChannelBinding.id == binding_id,
            ChannelBinding.user_id == user_id,
            ChannelBinding.is_active.is_(True),
        )
        binding = self.session.exec(statement).first()
        if binding is None:
            return False

        binding.is_active = False
        binding.unbound_at = datetime.now(UTC)
        self.session.add(binding)
        self.session.commit()
        return True

    def lookup_binding(
        self,
        channel_type: ChannelType,
        external_user_id: str,
    ) -> ChannelBinding | None:
        """Look up an active binding by channel type and external user ID."""
        return self._find_active_binding(channel_type, external_user_id)

    def _expire_code(self, code: str) -> None:
        """Manually expire a code (for testing purposes)."""
        entry = ChannelBindingService._otp_store.get(code)
        if entry is not None:
            entry["expires_at"] = 0

    def _find_active_binding(
        self, channel_type: ChannelType, external_user_id: str
    ) -> ChannelBinding | None:
        """Find an active binding for a given channel type and external user ID."""
        statement = select(ChannelBinding).where(
            ChannelBinding.channel_type == channel_type,
            ChannelBinding.external_user_id == external_user_id,
            ChannelBinding.is_active.is_(True),
        )
        return self.session.exec(statement).first()

    def _make_unique_code(self) -> str:
        """Generate a unique 6-digit code not currently in the store."""
        for _ in range(100):
            code = "".join(secrets.choice("0123456789") for _ in range(CODE_LENGTH))
            if code not in ChannelBindingService._otp_store:
                return code
        raise RuntimeError("Failed to generate unique OTP code")
