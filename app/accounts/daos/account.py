from sqlalchemy.orm import Session

from app.db.dao import CRUDDao
from app.accounts.models import Transactions
from app.accounts.serializers.account import (
    TransactionCreateSerializer,
    TransactionUpdateSerializer,
)


class TransactionDao(
    CRUDDao[Transactions, TransactionCreateSerializer, TransactionUpdateSerializer]
):
    def on_pre_create(
        self, db: Session, id: str, values: dict, orig_values: dict
    ) -> None:
        """Calculate total charge before creating transaction instance"""
        user_account = self.get(
            db, filters={"order_by": ["-created_at"], "account": values["account"]}
        )

        initial_final_balance = 0.0
        if user_account is not None:
            initial_final_balance = user_account.final_balance
        print(initial_final_balance)

        # Order by filter
        # Get recent final balance
        # Create new final balance
        # Enter into db
        # Write tests, lots of tests


transaction_dao = TransactionDao(Transactions)
