"""Audit service for tracking entity changes.

Provides methods to log create, update, delete, and reassign operations
for entities within a ledger.
"""

import uuid
from typing import Any

from sqlmodel import Session

from src.models.audit_log import AuditAction, AuditLog


class AuditService:
    """Service for creating and querying audit log entries."""

    def __init__(self, db: Session):
        self.db = db

    def log_create(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        new_value: dict[str, Any],
        ledger_id: uuid.UUID,
    ) -> AuditLog:
        """Log a CREATE action for an entity.

        Args:
            entity_type: Type of entity (e.g., "Account")
            entity_id: ID of the created entity
            new_value: The new entity state as a dict
            ledger_id: ID of the ledger for scoping

        Returns:
            The created AuditLog entry
        """
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.CREATE,
            old_value=None,
            new_value=new_value,
            extra_data=None,
            ledger_id=ledger_id,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def log_update(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        old_value: dict[str, Any],
        new_value: dict[str, Any],
        ledger_id: uuid.UUID,
    ) -> AuditLog:
        """Log an UPDATE action for an entity.

        Args:
            entity_type: Type of entity (e.g., "Account")
            entity_id: ID of the updated entity
            old_value: The previous entity state as a dict
            new_value: The new entity state as a dict
            ledger_id: ID of the ledger for scoping

        Returns:
            The created AuditLog entry
        """
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.UPDATE,
            old_value=old_value,
            new_value=new_value,
            extra_data=None,
            ledger_id=ledger_id,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def log_delete(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        old_value: dict[str, Any],
        ledger_id: uuid.UUID,
    ) -> AuditLog:
        """Log a DELETE action for an entity.

        Args:
            entity_type: Type of entity (e.g., "Account")
            entity_id: ID of the deleted entity
            old_value: The deleted entity state as a dict
            ledger_id: ID of the ledger for scoping

        Returns:
            The created AuditLog entry
        """
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.DELETE,
            old_value=old_value,
            new_value=None,
            extra_data=None,
            ledger_id=ledger_id,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def log_reassign(
        self,
        from_account_id: uuid.UUID,
        to_account_id: uuid.UUID,
        transaction_count: int,
        ledger_id: uuid.UUID,
    ) -> AuditLog:
        """Log a REASSIGN action for transaction reassignment.

        Args:
            from_account_id: ID of the source account (being deleted)
            to_account_id: ID of the target account (receiving transactions)
            transaction_count: Number of transactions reassigned
            ledger_id: ID of the ledger for scoping

        Returns:
            The created AuditLog entry
        """
        log = AuditLog(
            entity_type="Account",
            entity_id=from_account_id,
            action=AuditAction.REASSIGN,
            old_value=None,
            new_value=None,
            extra_data={
                "from_account_id": str(from_account_id),
                "to_account_id": str(to_account_id),
                "transaction_count": transaction_count,
            },
            ledger_id=ledger_id,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
