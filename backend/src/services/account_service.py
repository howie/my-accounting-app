"""Account service for business logic.

Based on contracts/account_service.md
Supports hierarchical account structure (up to 3 levels deep).
"""

import uuid
from decimal import Decimal

from sqlmodel import Session, func, select

from src.models.account import Account, AccountType
from src.models.transaction import Transaction
from src.schemas.account import AccountCreate, AccountTreeNode, AccountUpdate, CanDeleteResponse

MAX_DEPTH = 3  # Maximum hierarchy depth
SORT_ORDER_GAP = 1000  # Gap between sort_order values for easier insertions


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

        # Build children map
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
                sort_order=account.sort_order,
                children=child_nodes,
            )

        # Build tree starting from root accounts (parent_id is None)
        root_accounts = children_map.get(None, [])
        return [build_tree_node(root) for root in root_accounts]

    def can_delete(self, account_id: uuid.UUID, ledger_id: uuid.UUID) -> CanDeleteResponse:
        """Check if account can be deleted and return blocking info.

        Returns details about what prevents deletion if any.
        """
        account = self.session.exec(
            select(Account).where(
                Account.id == account_id, Account.ledger_id == ledger_id
            )
        ).first()

        if not account:
            raise ValueError("Account not found")

        has_children = self.has_children(account_id)
        has_transactions = self.has_transactions(account_id)

        child_count = 0
        transaction_count = 0

        if has_children:
            child_count = self.session.exec(
                select(func.count()).where(Account.parent_id == account_id)
            ).one()

        if has_transactions:
            transaction_count = self.session.exec(
                select(func.count()).where(
                    (Transaction.from_account_id == account_id)
                    | (Transaction.to_account_id == account_id)
                )
            ).one()

        can_delete = not has_children and not has_transactions and not account.is_system

        return CanDeleteResponse(
            can_delete=can_delete,
            has_children=has_children,
            has_transactions=has_transactions,
            transaction_count=transaction_count,
            child_count=child_count,
        )

    def get_replacement_candidates(
        self, account_id: uuid.UUID, ledger_id: uuid.UUID
    ) -> list[Account]:
        """Get accounts that can receive reassigned transactions.

        Returns accounts of the same type, excluding the account being deleted.
        """
        account = self.session.exec(
            select(Account).where(
                Account.id == account_id, Account.ledger_id == ledger_id
            )
        ).first()

        if not account:
            raise ValueError("Account not found")

        # Get all accounts of the same type that are not the current account
        candidates = self.session.exec(
            select(Account)
            .where(
                Account.ledger_id == ledger_id,
                Account.type == account.type,
                Account.id != account_id,
            )
            .order_by(Account.sort_order, Account.name)
        ).all()

        return list(candidates)

    def reassign_transactions(
        self, from_account_id: uuid.UUID, to_account_id: uuid.UUID, ledger_id: uuid.UUID
    ) -> int:
        """Reassign all transactions from one account to another.

        Returns the number of transactions moved.
        Raises ValueError if accounts are invalid or incompatible.
        """
        from_account = self.session.exec(
            select(Account).where(
                Account.id == from_account_id, Account.ledger_id == ledger_id
            )
        ).first()

        to_account = self.session.exec(
            select(Account).where(
                Account.id == to_account_id, Account.ledger_id == ledger_id
            )
        ).first()

        if not from_account:
            raise ValueError("Source account not found")

        if not to_account:
            raise ValueError("Target account not found")

        if from_account.type != to_account.type:
            raise ValueError("Cannot reassign to account of different type")

        if from_account_id == to_account_id:
            raise ValueError("Cannot reassign to the same account")

        # Count transactions before update
        count = self.session.exec(
            select(func.count()).where(
                (Transaction.from_account_id == from_account_id)
                | (Transaction.to_account_id == from_account_id)
            )
        ).one()

        # Update from_account_id references
        self.session.exec(
            select(Transaction).where(Transaction.from_account_id == from_account_id)
        )
        for txn in self.session.exec(
            select(Transaction).where(Transaction.from_account_id == from_account_id)
        ).all():
            txn.from_account_id = to_account_id
            self.session.add(txn)

        # Update to_account_id references
        for txn in self.session.exec(
            select(Transaction).where(Transaction.to_account_id == from_account_id)
        ).all():
            txn.to_account_id = to_account_id
            self.session.add(txn)

        self.session.commit()
        return count

    def reorder_accounts(
        self, ledger_id: uuid.UUID, parent_id: uuid.UUID | None, account_ids: list[uuid.UUID]
    ) -> int:
        """Reorder accounts within a parent.

        Updates sort_order for accounts in the given order.
        Returns the number of accounts updated.
        """
        # Verify all accounts exist and belong to the same parent
        accounts = self.session.exec(
            select(Account).where(
                Account.ledger_id == ledger_id,
                Account.parent_id == parent_id,
                Account.id.in_(account_ids),
            )
        ).all()

        account_map = {a.id: a for a in accounts}

        if len(account_map) != len(account_ids):
            raise ValueError("Some accounts not found or don't belong to the specified parent")

        # Update sort_order based on position in the list
        updated = 0
        for idx, account_id in enumerate(account_ids):
            account = account_map.get(account_id)
            if account:
                new_order = (idx + 1) * SORT_ORDER_GAP
                if account.sort_order != new_order:
                    account.sort_order = new_order
                    self.session.add(account)
                    updated += 1

        self.session.commit()
        return updated

    def get_transaction_count(self, account_id: uuid.UUID) -> int:
        """Get the number of transactions for an account."""
        return self.session.exec(
            select(func.count()).where(
                (Transaction.from_account_id == account_id)
                | (Transaction.to_account_id == account_id)
            )
        ).one()

    def get_child_count(self, account_id: uuid.UUID) -> int:
        """Get the number of child accounts."""
        return self.session.exec(
            select(func.count()).where(Account.parent_id == account_id)
        ).one()
