"""Account service for business logic.

Based on contracts/account_service.md
Supports hierarchical account structure (up to 3 levels deep).
"""

import uuid
from decimal import Decimal

from sqlmodel import Session, select, func

from src.models.account import Account, AccountType
from src.models.transaction import Transaction
from src.schemas.account import AccountCreate, AccountUpdate, AccountTreeNode

MAX_DEPTH = 3  # Maximum hierarchy depth


class AccountService:
    """Service for managing accounts within a ledger.

    Handles account CRUD operations with protection for system accounts
    and accounts with transactions.

    Supports hierarchical structure:
    - depth=1: Root level (no parent)
    - depth=2: Child of root
    - depth=3: Grandchild (max depth)
    """

    def __init__(self, session: Session) -> None:
        """Initialize service with database session."""
        self.session = session

    def create_account(self, ledger_id: uuid.UUID, data: AccountCreate) -> Account:
        """Create a new account in the ledger.

        Raises ValueError if:
        - Account name already exists in the ledger
        - Parent doesn't exist or belongs to different ledger
        - Parent has different account type
        - Depth would exceed MAX_DEPTH (3)
        """
        # Check for duplicate name
        existing = self.session.exec(
            select(Account).where(
                Account.ledger_id == ledger_id, Account.name == data.name
            )
        ).first()

        if existing:
            raise ValueError(f"Account with name '{data.name}' already exists")

        # Validate parent and calculate depth
        depth = 1
        parent_id = data.parent_id

        if parent_id is not None:
            parent = self.session.exec(
                select(Account).where(Account.id == parent_id)
            ).first()

            if not parent:
                raise ValueError("Parent account not found")

            if parent.ledger_id != ledger_id:
                raise ValueError("Parent account belongs to a different ledger")

            if parent.type != data.type:
                raise ValueError(
                    f"Child account type must match parent type ({parent.type.value})"
                )

            depth = parent.depth + 1
            if depth > MAX_DEPTH:
                raise ValueError(
                    f"Maximum hierarchy depth ({MAX_DEPTH}) exceeded"
                )

        account = Account(
            ledger_id=ledger_id,
            name=data.name,
            type=data.type,
            is_system=False,
            parent_id=parent_id,
            depth=depth,
        )
        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)
        return account

    def get_accounts(
        self, ledger_id: uuid.UUID, type_filter: AccountType | None = None
    ) -> list[Account]:
        """List all accounts for a ledger.

        Optionally filter by account type.
        """
        statement = select(Account).where(Account.ledger_id == ledger_id)

        if type_filter is not None:
            statement = statement.where(Account.type == type_filter)

        result = self.session.exec(statement)
        return list(result.all())

    def get_account(
        self, account_id: uuid.UUID, ledger_id: uuid.UUID
    ) -> Account | None:
        """Get a single account with calculated balance."""
        statement = select(Account).where(
            Account.id == account_id, Account.ledger_id == ledger_id
        )
        result = self.session.exec(statement)
        account = result.first()

        if account:
            # Update balance from transactions
            account.balance = self.calculate_balance(account_id)

        return account

    def update_account(
        self, account_id: uuid.UUID, ledger_id: uuid.UUID, data: AccountUpdate
    ) -> Account | None:
        """Update account name.

        Raises ValueError for system accounts or duplicate names.
        """
        account = self.session.exec(
            select(Account).where(
                Account.id == account_id, Account.ledger_id == ledger_id
            )
        ).first()

        if not account:
            return None

        # Cannot rename system accounts
        if account.is_system:
            raise ValueError("Cannot modify system account")

        if data.name is not None:
            # Check for duplicate name (except self)
            existing = self.session.exec(
                select(Account).where(
                    Account.ledger_id == ledger_id,
                    Account.name == data.name,
                    Account.id != account_id,
                )
            ).first()

            if existing:
                raise ValueError(f"Account with name '{data.name}' already exists")

            account.name = data.name

        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)
        return account

    def delete_account(self, account_id: uuid.UUID, ledger_id: uuid.UUID) -> bool:
        """Delete an account.

        Raises ValueError for system accounts, accounts with transactions,
        or accounts with children.
        Returns True if deleted, False if not found.
        """
        account = self.session.exec(
            select(Account).where(
                Account.id == account_id, Account.ledger_id == ledger_id
            )
        ).first()

        if not account:
            return False

        # Cannot delete system accounts
        if account.is_system:
            raise ValueError("Cannot delete system account")

        # Cannot delete accounts with children
        if self.has_children(account_id):
            raise ValueError("Cannot delete account that has child accounts")

        # Cannot delete accounts with transactions
        if self.has_transactions(account_id):
            raise ValueError("Cannot delete account that has transactions")

        self.session.delete(account)
        self.session.commit()
        return True

    def calculate_balance(self, account_id: uuid.UUID) -> Decimal:
        """Calculate account balance from all transactions.

        For accounts with children, this aggregates all descendant balances.

        For Asset: SUM(incoming) - SUM(outgoing) (what you have)
        For Liability: SUM(outgoing) - SUM(incoming) (what you owe)
            - When you charge to credit card (from liability), outgoing ↑, balance ↑
            - When you pay off (to liability), incoming ↑, balance ↓
        For Income: SUM(outgoing)  # Money flows OUT to assets
        For Expense: SUM(incoming) # Money flows IN from assets
        """
        account = self.session.get(Account, account_id)
        if not account:
            return Decimal("0")

        # Get all descendant account IDs (including self)
        descendant_ids = self.get_descendant_ids(account_id)

        # Sum of transactions where any descendant is the destination (incoming)
        incoming_result = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
                Transaction.to_account_id.in_(descendant_ids)
            )
        ).one()
        incoming = Decimal(str(incoming_result)) if incoming_result else Decimal("0")

        # Sum of transactions where any descendant is the source (outgoing)
        outgoing_result = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
                Transaction.from_account_id.in_(descendant_ids)
            )
        ).one()
        outgoing = Decimal(str(outgoing_result)) if outgoing_result else Decimal("0")

        if account.type == AccountType.ASSET:
            return incoming - outgoing
        elif account.type == AccountType.LIABILITY:
            return outgoing - incoming  # What you owe (positive when in debt)
        elif account.type == AccountType.INCOME:
            return outgoing  # Income "earns" by sending to assets
        else:  # EXPENSE
            return incoming  # Expense "spends" by receiving from assets

    def has_transactions(self, account_id: uuid.UUID) -> bool:
        """Check if account has any associated transactions."""
        count = self.session.exec(
            select(func.count()).where(
                (Transaction.from_account_id == account_id)
                | (Transaction.to_account_id == account_id)
            )
        ).one()
        return count > 0

    def has_children(self, account_id: uuid.UUID) -> bool:
        """Check if account has any child accounts."""
        count = self.session.exec(
            select(func.count()).where(Account.parent_id == account_id)
        ).one()
        return count > 0

    def can_have_transactions(self, account_id: uuid.UUID) -> bool:
        """Check if account can have transactions (must be a leaf account)."""
        return not self.has_children(account_id)

    def get_descendant_ids(self, account_id: uuid.UUID) -> list[uuid.UUID]:
        """Get all descendant account IDs including the account itself.

        Uses recursive query to get entire subtree.
        """
        result = [account_id]

        # Get direct children
        children = self.session.exec(
            select(Account.id).where(Account.parent_id == account_id)
        ).all()

        # Recursively get descendants of each child
        for child_id in children:
            result.extend(self.get_descendant_ids(child_id))

        return result

    def get_account_tree(
        self, ledger_id: uuid.UUID, type_filter: AccountType | None = None
    ) -> list[AccountTreeNode]:
        """Get hierarchical tree of accounts for a ledger.

        Returns only root-level accounts with nested children.
        Each node includes aggregated balance from all descendants.
        """
        # Get all accounts for the ledger
        statement = select(Account).where(Account.ledger_id == ledger_id)
        if type_filter is not None:
            statement = statement.where(Account.type == type_filter)

        accounts = list(self.session.exec(statement).all())

        # Build account lookup and children map
        account_map: dict[uuid.UUID, Account] = {a.id: a for a in accounts}
        children_map: dict[uuid.UUID | None, list[Account]] = {}

        for account in accounts:
            parent_key = account.parent_id
            if parent_key not in children_map:
                children_map[parent_key] = []
            children_map[parent_key].append(account)

        def build_tree_node(account: Account) -> AccountTreeNode:
            """Recursively build tree node with children."""
            children = children_map.get(account.id, [])
            child_nodes = [build_tree_node(child) for child in children]

            return AccountTreeNode(
                id=account.id,
                name=account.name,
                type=account.type,
                balance=self.calculate_balance(account.id),
                is_system=account.is_system,
                parent_id=account.parent_id,
                depth=account.depth,
                children=child_nodes,
            )

        # Build tree starting from root accounts (parent_id is None)
        root_accounts = children_map.get(None, [])
        return [build_tree_node(root) for root in root_accounts]
