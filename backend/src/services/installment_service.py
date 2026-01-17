from decimal import Decimal

from dateutil.relativedelta import relativedelta
from sqlmodel import Session

from src.models.advanced import InstallmentPlan
from src.models.transaction import Transaction, TransactionType
from src.schemas.advanced import InstallmentPlanCreate


class InstallmentService:
    def __init__(self, session: Session):
        self.session = session

    def create_installment_plan(self, data: InstallmentPlanCreate) -> InstallmentPlan:
        # Validate data
        if data.installment_count <= 1:
            raise ValueError("Installment count must be > 1")
        if data.total_amount <= 0:
            raise ValueError("Total amount must be positive")

        plan = InstallmentPlan.model_validate(data)
        self.session.add(plan)
        # Flush to get plan ID
        self.session.flush()

        # Get ledger_id from source account
        from src.models.account import Account

        src_account = self.session.get(Account, data.source_account_id)
        if not src_account:
            raise ValueError("Source account not found")

        # Generate transactions
        # Logic:
        # total 100, count 3. 33.33, 33.33, 33.34
        # base = 33.33
        # remainder = 0.01

        base_amount = (data.total_amount / data.installment_count).quantize(Decimal("0.01"))
        # Using basic quantization (ROUND_HALF_EVEN default) might not be exact floor.
        # Safer: int math on cents if strictly needed, but Decimal usually fine if we check remainder.

        # Let's verify sum
        current_sum = base_amount * data.installment_count
        remainder = data.total_amount - current_sum

        # We will add remainder to the last transaction (or distribute)

        for i in range(data.installment_count):
            amount = base_amount
            # Add remainder to the last one (simple)
            # Or distribute 0.01 to first N?
            # If remainder is negative (e.g. 10 / 3 -> 3.33 * 3 = 9.99, rem 0.01.
            # If 20 / 3 -> 6.67 * 3 = 20.01, rem -0.01)

            # Actually, standard is: first N get +0.01? Or last gets adjustment.
            # Let's assume standard rounding.
            # 100 / 3 = 33.3333 -> 33.33. Remainder 0.01.
            # Last txn gets +0.01.

            if i == data.installment_count - 1:
                amount += remainder

            txn_date = data.start_date + relativedelta(months=i)

            txn = Transaction(
                ledger_id=src_account.ledger_id,
                date=txn_date,
                description=f"{data.name} ({i + 1}/{data.installment_count})",
                amount=amount,
                from_account_id=data.source_account_id,
                to_account_id=data.dest_account_id,
                transaction_type=TransactionType.EXPENSE,  # Or whatever default, maybe need input? Assuming Expense for installment purchase
                installment_plan_id=plan.id,
                installment_number=i + 1,
                notes=f"Installment {i + 1} of {data.installment_count} for {data.name}",
            )
            self.session.add(txn)

        self.session.commit()
        self.session.refresh(plan)
        return plan
