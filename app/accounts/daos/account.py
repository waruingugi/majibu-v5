from sqlalchemy.orm import Session

from app.db.dao import CRUDDao
from app.accounts.models import Transactions
from app.accounts.serializers.account import (
    TransactionCreateSerializer,
    TransactionUpdateSerializer,
)
from app.accounts.constants import TransactionCashFlow


class TransactionDao(
    CRUDDao[Transactions, TransactionCreateSerializer, TransactionUpdateSerializer]
):
    def on_pre_create(
        self, db: Session, id: str, values: dict, orig_values: dict
    ) -> None:
        """Calculate total charge before creating transaction instance"""
        latest_transaction = self.get_or_none(
            db, {"order_by": ["-created_at"], "account": values["account"]}
        )

        initial_final_balance = 0.0
        charge = 0.0

        if latest_transaction:
            initial_final_balance = float(latest_transaction.final_balance)

        if values["cash_flow"] == TransactionCashFlow.INWARD.value:
            charge = values["amount"] - values["fee"] - values["tax"]
        else:  # If transaction is outward
            charge = values["amount"] + values["fee"] + values["tax"]

        values["final_balance"] = initial_final_balance + charge  # New final balance
        values["initial_balance"] = initial_final_balance  # Original balance
        values["charge"] = charge

    def get_user_balance(self, db: Session, *, account: str) -> float:
        latest_transaction = self.get_or_none(
            db, {"order_by": ["-created_at"], "account": account}
        )
        current_balance = 0.00
        if latest_transaction:
            current_balance = latest_transaction.final_balance

        return current_balance


transaction_dao = TransactionDao(Transactions)
