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
        user_account_transactions = self.search(
            db, {"order_by": ["-created_at"], "account": values["account"]}
        )

        initial_final_balance = 0.0
        charge = 0.0

        if user_account_transactions:
            user_account = user_account_transactions[0]
            initial_final_balance = float(user_account.final_balance)

        if values["cash_flow"] == TransactionCashFlow.INWARD.value:
            charge = values["amount"] - values["fee"] - values["tax"]
        else:  # If transaction is outward
            charge = values["amount"] + values["fee"] + values["tax"]

        values["final_balance"] = initial_final_balance + charge  # New final balance
        values["initial_balance"] = initial_final_balance  # Original balance
        values["charge"] = charge


transaction_dao = TransactionDao(Transactions)
