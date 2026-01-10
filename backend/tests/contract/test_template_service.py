"""Contract tests for TemplateService.

Tests the service interface contract for transaction templates.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.core.exceptions import NotFoundError, ValidationError
from src.models.account import AccountType
from src.models.transaction import TransactionType
from src.schemas.account import AccountCreate
from src.schemas.ledger import LedgerCreate
from src.schemas.transaction_template import (
    ApplyTemplateRequest,
    ReorderTemplatesRequest,
    TransactionTemplateCreate,
    TransactionTemplateUpdate,
)
from src.services.account_service import AccountService
from src.services.ledger_service import LedgerService
from src.services.template_service import TemplateService


class TestTemplateServiceContract:
    """Contract tests for TemplateService."""

    @pytest.fixture
    def ledger_service(self, session: Session) -> LedgerService:
        return LedgerService(session)

    @pytest.fixture
    def account_service(self, session: Session) -> AccountService:
        return AccountService(session)

    @pytest.fixture
    def service(self, session: Session) -> TemplateService:
        return TemplateService(session)

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def ledger_id(self, ledger_service: LedgerService, user_id: uuid.UUID) -> uuid.UUID:
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test Ledger", initial_balance=Decimal("1000.00"))
        )
        return ledger.id

    @pytest.fixture
    def cash_account_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        accounts = account_service.get_accounts(ledger_id)
        return next(a.id for a in accounts if a.name == "Cash")

    @pytest.fixture
    def expense_account_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )
        return account.id

    @pytest.fixture
    def income_account_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Salary", type=AccountType.INCOME)
        )
        return account.id

    @pytest.fixture
    def bank_account_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Bank", type=AccountType.ASSET)
        )
        return account.id

    # --- create_template ---

    def test_create_template_returns_template_with_id(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Creating a template returns a TransactionTemplate with a valid UUID id."""
        data = TransactionTemplateCreate(
            name="Lunch",
            transaction_type=TransactionType.EXPENSE,
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            amount=Decimal("50.00"),
            description="Daily lunch expense",
        )

        result = service.create_template(ledger_id, data)

        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)

    def test_create_template_stores_ledger_id(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Created template is associated with the provided ledger_id."""
        data = TransactionTemplateCreate(
            name="Test",
            transaction_type=TransactionType.EXPENSE,
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            amount=Decimal("50.00"),
            description="Test template",
        )

        result = service.create_template(ledger_id, data)

        assert result.ledger_id == ledger_id

    def test_create_template_stores_all_fields(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Created template stores all provided fields."""
        data = TransactionTemplateCreate(
            name="Monthly Rent",
            transaction_type=TransactionType.EXPENSE,
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            amount=Decimal("1500.00"),
            description="Monthly rent payment",
        )

        result = service.create_template(ledger_id, data)

        assert result.name == "Monthly Rent"
        assert result.transaction_type == TransactionType.EXPENSE
        assert result.from_account_id == cash_account_id
        assert result.to_account_id == expense_account_id
        assert result.amount == Decimal("1500.00")
        assert result.description == "Monthly rent payment"

    def test_create_template_has_timestamps(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Created template has created_at and updated_at timestamps."""
        data = TransactionTemplateCreate(
            name="Test",
            transaction_type=TransactionType.EXPENSE,
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            amount=Decimal("50.00"),
            description="Test",
        )

        result = service.create_template(ledger_id, data)

        assert result.created_at is not None
        assert result.updated_at is not None

    def test_create_template_assigns_sort_order(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Created templates get incrementing sort_order values."""
        template1 = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Template 1",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="First template",
            ),
        )
        template2 = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Template 2",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("75.00"),
                description="Second template",
            ),
        )

        assert template2.sort_order > template1.sort_order

    def test_create_template_duplicate_name_raises_error(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Creating a template with duplicate name in same ledger raises error."""
        data = TransactionTemplateCreate(
            name="Duplicate",
            transaction_type=TransactionType.EXPENSE,
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            amount=Decimal("50.00"),
            description="First template",
        )
        service.create_template(ledger_id, data)

        data2 = TransactionTemplateCreate(
            name="Duplicate",
            transaction_type=TransactionType.EXPENSE,
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            amount=Decimal("100.00"),
            description="Second template",
        )

        with pytest.raises(ValidationError, match="already exists"):
            service.create_template(ledger_id, data2)

    def test_create_template_same_accounts_raises_error(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
    ) -> None:
        """Creating a template with same from and to account raises error."""
        data = TransactionTemplateCreate(
            name="Invalid",
            transaction_type=TransactionType.TRANSFER,
            from_account_id=cash_account_id,
            to_account_id=cash_account_id,
            amount=Decimal("50.00"),
            description="Same account transfer",
        )

        with pytest.raises(ValidationError, match="different"):
            service.create_template(ledger_id, data)

    def test_create_template_invalid_account_raises_error(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
    ) -> None:
        """Creating a template with non-existent account raises error."""
        data = TransactionTemplateCreate(
            name="Invalid",
            transaction_type=TransactionType.EXPENSE,
            from_account_id=cash_account_id,
            to_account_id=uuid.uuid4(),  # Non-existent account
            amount=Decimal("50.00"),
            description="Invalid account",
        )

        with pytest.raises(ValidationError, match="not found"):
            service.create_template(ledger_id, data)

    # --- list_templates ---

    def test_list_templates_returns_empty_list_initially(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
    ) -> None:
        """list_templates returns empty list for ledger with no templates."""
        result = service.list_templates(ledger_id)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_list_templates_returns_created_templates(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """list_templates returns templates after creation."""
        service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Test",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="Test template",
            ),
        )

        result = service.list_templates(ledger_id)

        assert len(result) == 1
        assert result[0].name == "Test"

    def test_list_templates_ordered_by_sort_order(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """list_templates returns templates ordered by sort_order."""
        for i in range(3):
            service.create_template(
                ledger_id,
                TransactionTemplateCreate(
                    name=f"Template {i + 1}",
                    transaction_type=TransactionType.EXPENSE,
                    from_account_id=cash_account_id,
                    to_account_id=expense_account_id,
                    amount=Decimal(f"{(i + 1) * 10}.00"),
                    description=f"Template {i + 1}",
                ),
            )

        result = service.list_templates(ledger_id)

        assert len(result) == 3
        for i in range(len(result) - 1):
            assert result[i].sort_order < result[i + 1].sort_order

    # --- get_template ---

    def test_get_template_returns_template_by_id(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """get_template returns the template with the specified ID."""
        created = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Find Me",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="Find this template",
            ),
        )

        result = service.get_template(created.id, ledger_id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Find Me"

    def test_get_template_raises_for_nonexistent(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
    ) -> None:
        """get_template raises NotFoundError for non-existent template ID."""
        with pytest.raises(NotFoundError):
            service.get_template(uuid.uuid4(), ledger_id)

    def test_get_template_raises_for_other_ledger(
        self,
        service: TemplateService,
        ledger_service: LedgerService,
        ledger_id: uuid.UUID,
        user_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """get_template raises NotFoundError if template belongs to different ledger."""
        created = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Original Ledger",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="In original ledger",
            ),
        )

        other_ledger = ledger_service.create_ledger(user_id, LedgerCreate(name="Other"))

        with pytest.raises(NotFoundError):
            service.get_template(created.id, other_ledger.id)

    # --- update_template ---

    def test_update_template_changes_fields(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """update_template changes the template fields."""
        created = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Original",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="Original description",
            ),
        )

        result = service.update_template(
            created.id,
            ledger_id,
            TransactionTemplateUpdate(
                name="Updated",
                amount=Decimal("75.00"),
            ),
        )

        assert result.name == "Updated"
        assert result.amount == Decimal("75.00")
        # Unchanged fields should remain the same
        assert result.description == "Original description"

    def test_update_template_partial_update(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """update_template supports partial updates (only specified fields)."""
        created = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Original",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="Original description",
            ),
        )

        result = service.update_template(
            created.id,
            ledger_id,
            TransactionTemplateUpdate(description="Updated description"),
        )

        assert result.name == "Original"  # Unchanged
        assert result.amount == Decimal("50.00")  # Unchanged
        assert result.description == "Updated description"

    def test_update_template_raises_for_nonexistent(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
    ) -> None:
        """update_template raises NotFoundError for non-existent template."""
        with pytest.raises(NotFoundError):
            service.update_template(
                uuid.uuid4(),
                ledger_id,
                TransactionTemplateUpdate(name="New Name"),
            )

    def test_update_template_duplicate_name_raises_error(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """update_template raises error if new name already exists."""
        service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Existing",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="Existing template",
            ),
        )
        to_update = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="To Update",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("75.00"),
                description="Will be updated",
            ),
        )

        with pytest.raises(ValidationError, match="already exists"):
            service.update_template(
                to_update.id,
                ledger_id,
                TransactionTemplateUpdate(name="Existing"),
            )

    def test_update_template_same_accounts_raises_error(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """update_template raises error if from and to account become the same."""
        created = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Test",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="Test",
            ),
        )

        with pytest.raises(ValidationError, match="different"):
            service.update_template(
                created.id,
                ledger_id,
                TransactionTemplateUpdate(to_account_id=cash_account_id),
            )

    # --- delete_template ---

    def test_delete_template_removes_template(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """delete_template removes the template from the database."""
        created = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="To Delete",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="Will be deleted",
            ),
        )

        service.delete_template(created.id, ledger_id)

        with pytest.raises(NotFoundError):
            service.get_template(created.id, ledger_id)

    def test_delete_template_raises_for_nonexistent(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
    ) -> None:
        """delete_template raises NotFoundError for non-existent template."""
        with pytest.raises(NotFoundError):
            service.delete_template(uuid.uuid4(), ledger_id)

    # --- reorder_templates ---

    def test_reorder_templates_changes_order(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """reorder_templates changes the sort_order of templates."""
        template1 = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Template 1",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("10.00"),
                description="First",
            ),
        )
        template2 = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Template 2",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("20.00"),
                description="Second",
            ),
        )
        template3 = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Template 3",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("30.00"),
                description="Third",
            ),
        )

        # Reverse the order
        result = service.reorder_templates(
            ledger_id,
            ReorderTemplatesRequest(template_ids=[template3.id, template2.id, template1.id]),
        )

        assert result[0].id == template3.id
        assert result[1].id == template2.id
        assert result[2].id == template1.id

    def test_reorder_templates_mismatched_ids_raises_error(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """reorder_templates raises error if provided IDs don't match ledger templates."""
        service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Template 1",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("10.00"),
                description="First",
            ),
        )

        with pytest.raises(ValidationError, match="match"):
            service.reorder_templates(
                ledger_id,
                ReorderTemplatesRequest(template_ids=[uuid.uuid4()]),
            )

    # --- apply_template ---

    def test_apply_template_creates_transaction(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """apply_template creates a transaction from the template."""
        template = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Lunch",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("25.00"),
                description="Daily lunch",
            ),
        )

        transaction = service.apply_template(template.id, ledger_id)

        assert transaction is not None
        assert transaction.ledger_id == ledger_id
        assert transaction.amount == Decimal("25.00")
        assert transaction.description == "Daily lunch"
        assert transaction.from_account_id == cash_account_id
        assert transaction.to_account_id == expense_account_id
        assert transaction.transaction_type == TransactionType.EXPENSE

    def test_apply_template_uses_today_by_default(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """apply_template uses today's date when no date is provided."""
        template = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Test",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="Test",
            ),
        )

        transaction = service.apply_template(template.id, ledger_id)

        assert transaction.date == date.today()

    def test_apply_template_with_custom_date(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """apply_template uses provided date when specified."""
        template = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Test",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="Test",
            ),
        )

        transaction = service.apply_template(
            template.id,
            ledger_id,
            ApplyTemplateRequest(date="2024-06-15"),
        )

        assert transaction.date == date(2024, 6, 15)

    def test_apply_template_with_notes(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """apply_template includes notes in the created transaction."""
        template = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Test",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="Test",
            ),
        )

        transaction = service.apply_template(
            template.id,
            ledger_id,
            ApplyTemplateRequest(notes="Special occasion"),
        )

        assert transaction.notes == "Special occasion"

    def test_apply_template_raises_for_nonexistent(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
    ) -> None:
        """apply_template raises NotFoundError for non-existent template."""
        with pytest.raises(NotFoundError):
            service.apply_template(uuid.uuid4(), ledger_id)

    def test_apply_template_invalid_date_raises_error(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """apply_template raises error for invalid date format."""
        template = service.create_template(
            ledger_id,
            TransactionTemplateCreate(
                name="Test",
                transaction_type=TransactionType.EXPENSE,
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                amount=Decimal("50.00"),
                description="Test",
            ),
        )

        with pytest.raises(ValidationError, match="date"):
            service.apply_template(
                template.id,
                ledger_id,
                ApplyTemplateRequest(date="invalid-date"),
            )


class TestTemplateServiceLimits:
    """Tests for template service limits and constraints."""

    @pytest.fixture
    def ledger_service(self, session: Session) -> LedgerService:
        return LedgerService(session)

    @pytest.fixture
    def account_service(self, session: Session) -> AccountService:
        return AccountService(session)

    @pytest.fixture
    def service(self, session: Session) -> TemplateService:
        return TemplateService(session)

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def ledger_id(self, ledger_service: LedgerService, user_id: uuid.UUID) -> uuid.UUID:
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test Ledger", initial_balance=Decimal("1000.00"))
        )
        return ledger.id

    @pytest.fixture
    def cash_account_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        accounts = account_service.get_accounts(ledger_id)
        return next(a.id for a in accounts if a.name == "Cash")

    @pytest.fixture
    def expense_account_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )
        return account.id

    def test_create_template_limit_enforcement(
        self,
        service: TemplateService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Creating more than 50 templates raises validation error."""
        # Create 50 templates
        for i in range(50):
            service.create_template(
                ledger_id,
                TransactionTemplateCreate(
                    name=f"Template {i + 1}",
                    transaction_type=TransactionType.EXPENSE,
                    from_account_id=cash_account_id,
                    to_account_id=expense_account_id,
                    amount=Decimal("10.00"),
                    description=f"Template number {i + 1}",
                ),
            )

        # 51st template should fail
        with pytest.raises(ValidationError, match="limit"):
            service.create_template(
                ledger_id,
                TransactionTemplateCreate(
                    name="Template 51",
                    transaction_type=TransactionType.EXPENSE,
                    from_account_id=cash_account_id,
                    to_account_id=expense_account_id,
                    amount=Decimal("10.00"),
                    description="One too many",
                ),
            )
