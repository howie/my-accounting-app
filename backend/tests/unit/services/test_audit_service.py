"""Unit tests for AuditService.

Tests the audit logging functionality for entity CRUD operations.
"""

import uuid
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.models.audit_log import AuditAction, AuditLog
from src.schemas.ledger import LedgerCreate
from src.services.audit_service import AuditService
from src.services.ledger_service import LedgerService


class TestAuditServiceContract:
    """Contract tests for AuditService."""

    @pytest.fixture
    def service(self, session: Session) -> AuditService:
        return AuditService(session)

    @pytest.fixture
    def ledger_service(self, session: Session) -> LedgerService:
        return LedgerService(session)

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def ledger_id(self, ledger_service: LedgerService, user_id: uuid.UUID) -> uuid.UUID:
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test Ledger", initial_balance=Decimal("1000.00"))
        )
        return ledger.id

    # --- log_create ---

    def test_log_create_returns_audit_log(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_create returns an AuditLog with valid ID."""
        entity_id = uuid.uuid4()
        new_value = {"name": "Test Account", "type": "ASSET"}

        result = service.log_create(
            entity_type="Account",
            entity_id=entity_id,
            new_value=new_value,
            ledger_id=ledger_id,
        )

        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)
        assert isinstance(result, AuditLog)

    def test_log_create_stores_entity_info(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_create stores entity_type and entity_id correctly."""
        entity_id = uuid.uuid4()
        new_value = {"name": "Cash", "type": "ASSET"}

        result = service.log_create(
            entity_type="Account",
            entity_id=entity_id,
            new_value=new_value,
            ledger_id=ledger_id,
        )

        assert result.entity_type == "Account"
        assert result.entity_id == entity_id

    def test_log_create_stores_action_as_create(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_create sets action to CREATE."""
        result = service.log_create(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            new_value={"name": "Test"},
            ledger_id=ledger_id,
        )

        assert result.action == AuditAction.CREATE

    def test_log_create_stores_new_value(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_create stores the new_value as JSON."""
        new_value = {
            "name": "Bank Account",
            "type": "ASSET",
            "balance": "5000.00",
        }

        result = service.log_create(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            new_value=new_value,
            ledger_id=ledger_id,
        )

        assert result.new_value == new_value
        assert result.new_value["name"] == "Bank Account"

    def test_log_create_has_null_old_value(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_create sets old_value to None for new entities."""
        result = service.log_create(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            new_value={"name": "New"},
            ledger_id=ledger_id,
        )

        assert result.old_value is None

    def test_log_create_stores_ledger_id(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_create associates the log with the correct ledger."""
        result = service.log_create(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            new_value={"name": "Test"},
            ledger_id=ledger_id,
        )

        assert result.ledger_id == ledger_id

    def test_log_create_has_timestamp(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_create adds a timestamp."""
        result = service.log_create(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            new_value={"name": "Test"},
            ledger_id=ledger_id,
        )

        assert result.timestamp is not None

    # --- log_update ---

    def test_log_update_returns_audit_log(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_update returns an AuditLog with valid ID."""
        result = service.log_update(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            old_value={"name": "Old Name"},
            new_value={"name": "New Name"},
            ledger_id=ledger_id,
        )

        assert result.id is not None
        assert isinstance(result, AuditLog)

    def test_log_update_stores_action_as_update(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_update sets action to UPDATE."""
        result = service.log_update(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            old_value={"name": "Old"},
            new_value={"name": "New"},
            ledger_id=ledger_id,
        )

        assert result.action == AuditAction.UPDATE

    def test_log_update_stores_both_values(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_update stores both old_value and new_value."""
        old_value = {"name": "Original Name", "description": "Old desc"}
        new_value = {"name": "Updated Name", "description": "New desc"}

        result = service.log_update(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            old_value=old_value,
            new_value=new_value,
            ledger_id=ledger_id,
        )

        assert result.old_value == old_value
        assert result.new_value == new_value

    def test_log_update_preserves_entity_info(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_update stores entity_type and entity_id."""
        entity_id = uuid.uuid4()

        result = service.log_update(
            entity_type="Transaction",
            entity_id=entity_id,
            old_value={"amount": "100.00"},
            new_value={"amount": "150.00"},
            ledger_id=ledger_id,
        )

        assert result.entity_type == "Transaction"
        assert result.entity_id == entity_id

    # --- log_delete ---

    def test_log_delete_returns_audit_log(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_delete returns an AuditLog with valid ID."""
        result = service.log_delete(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            old_value={"name": "Deleted Account"},
            ledger_id=ledger_id,
        )

        assert result.id is not None
        assert isinstance(result, AuditLog)

    def test_log_delete_stores_action_as_delete(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_delete sets action to DELETE."""
        result = service.log_delete(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            old_value={"name": "To Delete"},
            ledger_id=ledger_id,
        )

        assert result.action == AuditAction.DELETE

    def test_log_delete_stores_old_value(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_delete stores the old_value for deleted entity."""
        old_value = {
            "name": "Deleted Account",
            "type": "EXPENSE",
            "balance": "0.00",
        }

        result = service.log_delete(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            old_value=old_value,
            ledger_id=ledger_id,
        )

        assert result.old_value == old_value

    def test_log_delete_has_null_new_value(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_delete sets new_value to None for deleted entities."""
        result = service.log_delete(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            old_value={"name": "Gone"},
            ledger_id=ledger_id,
        )

        assert result.new_value is None

    # --- log_reassign ---

    def test_log_reassign_returns_audit_log(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_reassign returns an AuditLog with valid ID."""
        result = service.log_reassign(
            from_account_id=uuid.uuid4(),
            to_account_id=uuid.uuid4(),
            transaction_count=5,
            ledger_id=ledger_id,
        )

        assert result.id is not None
        assert isinstance(result, AuditLog)

    def test_log_reassign_stores_action_as_reassign(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_reassign sets action to REASSIGN."""
        result = service.log_reassign(
            from_account_id=uuid.uuid4(),
            to_account_id=uuid.uuid4(),
            transaction_count=10,
            ledger_id=ledger_id,
        )

        assert result.action == AuditAction.REASSIGN

    def test_log_reassign_stores_entity_type_as_account(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_reassign sets entity_type to Account."""
        result = service.log_reassign(
            from_account_id=uuid.uuid4(),
            to_account_id=uuid.uuid4(),
            transaction_count=3,
            ledger_id=ledger_id,
        )

        assert result.entity_type == "Account"

    def test_log_reassign_uses_from_account_as_entity_id(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_reassign uses from_account_id as entity_id."""
        from_account = uuid.uuid4()

        result = service.log_reassign(
            from_account_id=from_account,
            to_account_id=uuid.uuid4(),
            transaction_count=7,
            ledger_id=ledger_id,
        )

        assert result.entity_id == from_account

    def test_log_reassign_stores_extra_data(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_reassign stores reassignment details in extra_data."""
        from_account = uuid.uuid4()
        to_account = uuid.uuid4()

        result = service.log_reassign(
            from_account_id=from_account,
            to_account_id=to_account,
            transaction_count=15,
            ledger_id=ledger_id,
        )

        assert result.extra_data is not None
        assert result.extra_data["from_account_id"] == str(from_account)
        assert result.extra_data["to_account_id"] == str(to_account)
        assert result.extra_data["transaction_count"] == 15

    def test_log_reassign_has_null_old_and_new_value(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_reassign sets old_value and new_value to None."""
        result = service.log_reassign(
            from_account_id=uuid.uuid4(),
            to_account_id=uuid.uuid4(),
            transaction_count=5,
            ledger_id=ledger_id,
        )

        assert result.old_value is None
        assert result.new_value is None


class TestAuditServiceEdgeCases:
    """Edge case tests for AuditService."""

    @pytest.fixture
    def service(self, session: Session) -> AuditService:
        return AuditService(session)

    @pytest.fixture
    def ledger_service(self, session: Session) -> LedgerService:
        return LedgerService(session)

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def ledger_id(self, ledger_service: LedgerService, user_id: uuid.UUID) -> uuid.UUID:
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test Ledger")
        )
        return ledger.id

    def test_log_create_with_complex_nested_value(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_create handles complex nested JSON values."""
        new_value = {
            "name": "Complex Entity",
            "metadata": {
                "tags": ["tag1", "tag2"],
                "config": {"enabled": True, "settings": [1, 2, 3]},
            },
            "amounts": ["100.00", "200.00"],
        }

        result = service.log_create(
            entity_type="CustomEntity",
            entity_id=uuid.uuid4(),
            new_value=new_value,
            ledger_id=ledger_id,
        )

        assert result.new_value == new_value
        assert result.new_value["metadata"]["tags"] == ["tag1", "tag2"]

    def test_log_update_with_empty_values(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_update handles empty dict values."""
        result = service.log_update(
            entity_type="Account",
            entity_id=uuid.uuid4(),
            old_value={},
            new_value={},
            ledger_id=ledger_id,
        )

        assert result.old_value == {}
        assert result.new_value == {}

    def test_multiple_logs_for_same_entity(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Multiple audit logs can be created for the same entity."""
        entity_id = uuid.uuid4()

        create_log = service.log_create(
            entity_type="Account",
            entity_id=entity_id,
            new_value={"name": "Initial"},
            ledger_id=ledger_id,
        )

        update_log = service.log_update(
            entity_type="Account",
            entity_id=entity_id,
            old_value={"name": "Initial"},
            new_value={"name": "Updated"},
            ledger_id=ledger_id,
        )

        delete_log = service.log_delete(
            entity_type="Account",
            entity_id=entity_id,
            old_value={"name": "Updated"},
            ledger_id=ledger_id,
        )

        assert create_log.id != update_log.id != delete_log.id
        assert create_log.action == AuditAction.CREATE
        assert update_log.action == AuditAction.UPDATE
        assert delete_log.action == AuditAction.DELETE

    def test_log_reassign_with_zero_transactions(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_reassign handles zero transaction count."""
        result = service.log_reassign(
            from_account_id=uuid.uuid4(),
            to_account_id=uuid.uuid4(),
            transaction_count=0,
            ledger_id=ledger_id,
        )

        assert result.extra_data["transaction_count"] == 0

    def test_different_entity_types(
        self,
        service: AuditService,
        ledger_id: uuid.UUID,
    ) -> None:
        """log_create works with different entity types."""
        entity_types = ["Account", "Transaction", "Ledger", "Template"]

        for entity_type in entity_types:
            result = service.log_create(
                entity_type=entity_type,
                entity_id=uuid.uuid4(),
                new_value={"test": True},
                ledger_id=ledger_id,
            )
            assert result.entity_type == entity_type
