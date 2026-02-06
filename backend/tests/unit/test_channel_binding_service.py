"""Unit tests for ChannelBindingService.

Tests OTP generation, verification, bind/unbind logic, and duplicate binding rejection.
Per Constitution Principle II: Tests written BEFORE implementation.
"""

import uuid

import pytest
from sqlmodel import Session

from src.models.channel_binding import ChannelType
from src.models.ledger import Ledger
from src.models.user import User


@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(email="test@example.com", display_name="Test User")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def ledger(session: Session, user: User) -> Ledger:
    """Create a test ledger."""
    ledger = Ledger(
        name="Test Ledger",
        description="For testing",
        currency="TWD",
        user_id=user.id,
    )
    session.add(ledger)
    session.commit()
    session.refresh(ledger)
    return ledger


def _get_service(session: Session):
    """Import and create ChannelBindingService."""
    from src.services.channel_binding_service import ChannelBindingService

    return ChannelBindingService(session)


class TestOTPGeneration:
    """Tests for OTP code generation."""

    def test_generate_code_returns_6_digit_string(self, session: Session, user: User):
        service = _get_service(session)
        code = service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)
        assert len(code) == 6
        assert code.isdigit()

    def test_generate_code_with_ledger_id(self, session: Session, user: User, ledger: Ledger):
        service = _get_service(session)
        code = service.generate_code(
            user_id=user.id,
            channel_type=ChannelType.TELEGRAM,
            default_ledger_id=ledger.id,
        )
        assert len(code) == 6
        assert code.isdigit()

    def test_generate_code_unique_per_call(self, session: Session, user: User):
        service = _get_service(session)
        codes = set()
        for _ in range(10):
            code = service.generate_code(user_id=user.id, channel_type=ChannelType.LINE)
            codes.add(code)
        # At least some should be different (probabilistically)
        assert len(codes) > 1


class TestOTPVerification:
    """Tests for OTP code verification."""

    def test_verify_valid_code(self, session: Session, user: User):
        service = _get_service(session)
        code = service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)
        binding = service.verify_code(
            code=code,
            external_user_id="telegram_123",
            display_name="Test Telegram",
        )
        assert binding is not None
        assert binding.user_id == user.id
        assert binding.channel_type == ChannelType.TELEGRAM
        assert binding.external_user_id == "telegram_123"
        assert binding.is_active is True

    def test_verify_wrong_code_returns_none(self, session: Session, user: User):
        service = _get_service(session)
        service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)
        result = service.verify_code(
            code="000000",
            external_user_id="telegram_123",
        )
        assert result is None

    def test_verify_code_consumed_after_use(self, session: Session, user: User):
        service = _get_service(session)
        code = service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)
        service.verify_code(code=code, external_user_id="telegram_123")
        # Second use should fail
        result = service.verify_code(code=code, external_user_id="telegram_456")
        assert result is None

    def test_verify_expired_code_returns_none(self, session: Session, user: User):
        service = _get_service(session)
        code = service.generate_code(
            user_id=user.id,
            channel_type=ChannelType.TELEGRAM,
        )
        # Manually expire the code
        service._expire_code(code)
        result = service.verify_code(code=code, external_user_id="telegram_123")
        assert result is None


class TestBindUnbind:
    """Tests for bind and unbind operations."""

    def test_list_bindings_empty(self, session: Session, user: User):
        service = _get_service(session)
        bindings = service.list_bindings(user_id=user.id)
        assert bindings == []

    def test_list_bindings_after_bind(self, session: Session, user: User):
        service = _get_service(session)
        code = service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)
        service.verify_code(code=code, external_user_id="telegram_123")
        bindings = service.list_bindings(user_id=user.id)
        assert len(bindings) == 1
        assert bindings[0].channel_type == ChannelType.TELEGRAM

    def test_unbind_sets_inactive(self, session: Session, user: User):
        service = _get_service(session)
        code = service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)
        binding = service.verify_code(code=code, external_user_id="telegram_123")
        assert binding is not None

        result = service.unbind(binding_id=binding.id, user_id=user.id)
        assert result is True

        bindings = service.list_bindings(user_id=user.id)
        assert len(bindings) == 0  # Active only by default

    def test_unbind_sets_unbound_at(self, session: Session, user: User):
        service = _get_service(session)
        code = service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)
        binding = service.verify_code(code=code, external_user_id="telegram_123")
        assert binding is not None

        service.unbind(binding_id=binding.id, user_id=user.id)
        session.refresh(binding)
        assert binding.is_active is False
        assert binding.unbound_at is not None

    def test_unbind_nonexistent_returns_false(self, session: Session, user: User):
        service = _get_service(session)
        result = service.unbind(binding_id=uuid.uuid4(), user_id=user.id)
        assert result is False

    def test_unbind_other_users_binding_returns_false(self, session: Session, user: User):
        other_user = User(email="other@example.com")
        session.add(other_user)
        session.commit()

        service = _get_service(session)
        code = service.generate_code(user_id=other_user.id, channel_type=ChannelType.TELEGRAM)
        binding = service.verify_code(code=code, external_user_id="telegram_other")
        assert binding is not None

        result = service.unbind(binding_id=binding.id, user_id=user.id)
        assert result is False


class TestDuplicateBinding:
    """Tests for duplicate binding rejection."""

    def test_duplicate_active_binding_rejected(self, session: Session, user: User):
        service = _get_service(session)
        # First binding
        code1 = service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)
        binding1 = service.verify_code(code=code1, external_user_id="telegram_123")
        assert binding1 is not None

        # Second user tries to bind same external account
        other_user = User(email="other@example.com")
        session.add(other_user)
        session.commit()

        code2 = service.generate_code(user_id=other_user.id, channel_type=ChannelType.TELEGRAM)
        binding2 = service.verify_code(code=code2, external_user_id="telegram_123")
        assert binding2 is None  # Should be rejected

    def test_can_rebind_after_unbind(self, session: Session, user: User):
        service = _get_service(session)
        # Bind
        code1 = service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)
        binding1 = service.verify_code(code=code1, external_user_id="telegram_123")
        assert binding1 is not None
        # Unbind
        service.unbind(binding_id=binding1.id, user_id=user.id)
        # Rebind
        code2 = service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)
        binding2 = service.verify_code(code=code2, external_user_id="telegram_123")
        assert binding2 is not None
        assert binding2.id != binding1.id


class TestLookupBinding:
    """Tests for looking up bindings by external user ID."""

    def test_lookup_by_external_id(self, session: Session, user: User):
        service = _get_service(session)
        code = service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)
        service.verify_code(code=code, external_user_id="telegram_123")

        binding = service.lookup_binding(
            channel_type=ChannelType.TELEGRAM,
            external_user_id="telegram_123",
        )
        assert binding is not None
        assert binding.user_id == user.id

    def test_lookup_nonexistent_returns_none(self, session: Session):
        service = _get_service(session)
        binding = service.lookup_binding(
            channel_type=ChannelType.TELEGRAM,
            external_user_id="nonexistent",
        )
        assert binding is None
