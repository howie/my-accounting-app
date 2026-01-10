"""Transaction Template Service.

Business logic for managing transaction templates (CRUD operations).
Based on spec.md from 004-transaction-entry feature.
"""

import uuid
from datetime import UTC, date, datetime

from sqlmodel import Session, func, select

from src.core.exceptions import NotFoundError, ValidationError
from src.models.account import Account
from src.models.transaction import Transaction
from src.models.transaction_template import TransactionTemplate
from src.schemas.transaction_template import (
    ApplyTemplateRequest,
    ReorderTemplatesRequest,
    TransactionTemplateCreate,
    TransactionTemplateUpdate,
)

# Maximum number of templates per ledger
MAX_TEMPLATES_PER_LEDGER = 50


class TemplateService:
    """Service for managing transaction templates."""

    def __init__(self, session: Session):
        self.session = session

    def list_templates(
        self,
        ledger_id: uuid.UUID,
    ) -> list[TransactionTemplate]:
        """List all templates for a ledger, ordered by sort_order.

        Args:
            ledger_id: The ledger ID

        Returns:
            List of templates sorted by sort_order
        """
        stmt = (
            select(TransactionTemplate)
            .where(TransactionTemplate.ledger_id == ledger_id)
            .order_by(TransactionTemplate.sort_order)
        )
        result = self.session.exec(stmt)
        return list(result.all())

    def get_template(
        self,
        template_id: uuid.UUID,
        ledger_id: uuid.UUID,
    ) -> TransactionTemplate:
        """Get a single template by ID.

        Args:
            template_id: The template ID
            ledger_id: The ledger ID (for authorization)

        Returns:
            The template

        Raises:
            NotFoundError: If template not found
        """
        stmt = select(TransactionTemplate).where(
            TransactionTemplate.id == template_id,
            TransactionTemplate.ledger_id == ledger_id,
        )
        template = self.session.exec(stmt).first()

        if not template:
            raise NotFoundError(f"Template {template_id} not found")

        return template

    def create_template(
        self,
        ledger_id: uuid.UUID,
        data: TransactionTemplateCreate,
    ) -> TransactionTemplate:
        """Create a new transaction template.

        Args:
            ledger_id: The ledger ID
            data: Template creation data

        Returns:
            The created template

        Raises:
            ValidationError: If validation fails (limit reached, duplicate name, same accounts)
        """
        # Check template limit
        count_stmt = (
            select(func.count())
            .select_from(TransactionTemplate)
            .where(TransactionTemplate.ledger_id == ledger_id)
        )
        count = self.session.exec(count_stmt).one() or 0

        if count >= MAX_TEMPLATES_PER_LEDGER:
            raise ValidationError(
                f"Template limit reached. Maximum {MAX_TEMPLATES_PER_LEDGER} templates per ledger."
            )

        # Check unique name per ledger
        name_stmt = select(TransactionTemplate).where(
            TransactionTemplate.ledger_id == ledger_id,
            TransactionTemplate.name == data.name,
        )
        existing = self.session.exec(name_stmt).first()
        if existing:
            raise ValidationError(f"Template name '{data.name}' already exists in this ledger")

        # Validate from_account_id != to_account_id
        if data.from_account_id == data.to_account_id:
            raise ValidationError("From and To accounts must be different")

        # Validate accounts exist and belong to ledger
        self._validate_accounts(ledger_id, data.from_account_id, data.to_account_id)

        # Get next sort_order
        max_order_stmt = select(func.max(TransactionTemplate.sort_order)).where(
            TransactionTemplate.ledger_id == ledger_id
        )
        max_order = self.session.exec(max_order_stmt).one() or 0

        template = TransactionTemplate(
            ledger_id=ledger_id,
            name=data.name,
            transaction_type=data.transaction_type,
            from_account_id=data.from_account_id,
            to_account_id=data.to_account_id,
            amount=data.amount,
            description=data.description,
            sort_order=max_order + 1,
        )

        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)

        return template

    def update_template(
        self,
        template_id: uuid.UUID,
        ledger_id: uuid.UUID,
        data: TransactionTemplateUpdate,
    ) -> TransactionTemplate:
        """Update an existing template.

        Args:
            template_id: The template ID
            ledger_id: The ledger ID
            data: Update data (partial)

        Returns:
            The updated template

        Raises:
            NotFoundError: If template not found
            ValidationError: If validation fails
        """
        template = self.get_template(template_id, ledger_id)

        # Check unique name if name is being updated
        if data.name is not None and data.name != template.name:
            name_stmt = select(TransactionTemplate).where(
                TransactionTemplate.ledger_id == ledger_id,
                TransactionTemplate.name == data.name,
                TransactionTemplate.id != template_id,
            )
            existing = self.session.exec(name_stmt).first()
            if existing:
                raise ValidationError(f"Template name '{data.name}' already exists in this ledger")

        # Determine final from/to account IDs
        from_account_id = (
            data.from_account_id if data.from_account_id is not None else template.from_account_id
        )
        to_account_id = (
            data.to_account_id if data.to_account_id is not None else template.to_account_id
        )

        # Validate from_account_id != to_account_id
        if from_account_id == to_account_id:
            raise ValidationError("From and To accounts must be different")

        # Validate accounts if changed
        if data.from_account_id is not None or data.to_account_id is not None:
            self._validate_accounts(ledger_id, from_account_id, to_account_id)

        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)

        template.updated_at = datetime.now(UTC)

        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)

        return template

    def delete_template(
        self,
        template_id: uuid.UUID,
        ledger_id: uuid.UUID,
    ) -> None:
        """Delete a template.

        Args:
            template_id: The template ID
            ledger_id: The ledger ID

        Raises:
            NotFoundError: If template not found
        """
        template = self.get_template(template_id, ledger_id)
        self.session.delete(template)
        self.session.commit()

    def reorder_templates(
        self,
        ledger_id: uuid.UUID,
        data: ReorderTemplatesRequest,
    ) -> list[TransactionTemplate]:
        """Reorder templates.

        Args:
            ledger_id: The ledger ID
            data: Reorder request with template IDs in desired order

        Returns:
            The reordered templates

        Raises:
            ValidationError: If template IDs don't match ledger templates
        """
        # Get all templates for ledger
        templates = self.list_templates(ledger_id)
        template_ids = {t.id for t in templates}

        # Validate provided IDs
        provided_ids = set(data.template_ids)
        if provided_ids != template_ids:
            raise ValidationError("Template IDs must match exactly the templates in this ledger")

        # Update sort_order for each template
        for new_order, template_id in enumerate(data.template_ids):
            template = self.session.get(TransactionTemplate, template_id)
            if template:
                template.sort_order = new_order
                template.updated_at = datetime.now(UTC)

        self.session.commit()

        return self.list_templates(ledger_id)

    def apply_template(
        self,
        template_id: uuid.UUID,
        ledger_id: uuid.UUID,
        data: ApplyTemplateRequest | None = None,
    ) -> Transaction:
        """Apply a template to create a new transaction.

        Args:
            template_id: The template ID
            ledger_id: The ledger ID
            data: Optional apply request with date override and notes

        Returns:
            The created transaction

        Raises:
            NotFoundError: If template not found
            ValidationError: If referenced accounts no longer exist
        """
        template = self.get_template(template_id, ledger_id)

        # Validate accounts still exist
        try:
            self._validate_accounts(ledger_id, template.from_account_id, template.to_account_id)
        except ValidationError:
            raise ValidationError(
                "An account referenced by this template has been deleted. "
                "Please edit or delete this template."
            )

        # Determine transaction date
        transaction_date = date.today()
        if data and data.date:
            try:
                transaction_date = date.fromisoformat(data.date)
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

        # Create transaction from template
        transaction = Transaction(
            ledger_id=ledger_id,
            date=transaction_date,
            description=template.description,
            amount=template.amount,
            from_account_id=template.from_account_id,
            to_account_id=template.to_account_id,
            transaction_type=template.transaction_type,
            notes=data.notes if data else None,
        )

        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)

        return transaction

    def _validate_accounts(
        self,
        ledger_id: uuid.UUID,
        from_account_id: uuid.UUID,
        to_account_id: uuid.UUID,
    ) -> None:
        """Validate that accounts exist and belong to the ledger.

        Args:
            ledger_id: The ledger ID
            from_account_id: The from account ID
            to_account_id: The to account ID

        Raises:
            ValidationError: If accounts don't exist or don't belong to ledger
        """
        for account_id, label in [
            (from_account_id, "From account"),
            (to_account_id, "To account"),
        ]:
            stmt = select(Account).where(
                Account.id == account_id,
                Account.ledger_id == ledger_id,
            )
            result = self.session.exec(stmt).first()
            if not result:
                raise ValidationError(f"{label} not found in this ledger")
