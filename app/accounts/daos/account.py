from sqlalchemy.orm import Session

from app.db.dao import CRUDDao
from app.accounts.models import Transactions
from app.accounts.serializers.account import (
    TransactionCreateSerializer,
    TransactionUpdateSerializer,
)
from app.accounts.constants import TransactionCashFlow, TransactionServices
from app.accounts.constants import MPESA_PAYMENT_DEPOSIT, MPESA_PAYMENT_WITHDRAW

from app.notifications.daos.notifications import notifications_dao
from app.notifications.serializers.notifications import CreateNotificationSerializer
from app.notifications.constants import NotificationChannels, NotificationTypes


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
            values["final_balance"] = (
                initial_final_balance + charge
            )  # New final balance
        else:  # If transaction is outward
            charge = values["amount"] + values["fee"] + values["tax"]
            values["final_balance"] = (
                initial_final_balance - charge
            )  # New final balance

        values["initial_balance"] = initial_final_balance  # Original balance
        values["charge"] = charge

    def on_post_create(self, db: Session, db_obj: Transactions) -> None:
        """Send notifications on new transactions to their wallet"""
        channel = NotificationChannels.SMS.value
        phone = db_obj.account
        message = type = ""

        if (
            db_obj.cash_flow == TransactionCashFlow.INWARD.value
            and db_obj.service == TransactionServices.MPESA.value
        ):  # Means if the transaction is an M-Pesa Deposit
            message = MPESA_PAYMENT_DEPOSIT.format(
                db_obj.amount, db_obj.account, db_obj.final_balance
            )
            type = NotificationTypes.DEPOSIT.value

        if (
            db_obj.cash_flow == TransactionCashFlow.OUTWARD.value
            and db_obj.service == TransactionServices.MPESA.value
        ):  # Means if the transaction is an M-Pesa Deposit
            message = MPESA_PAYMENT_WITHDRAW.format(
                db_obj.amount, db_obj.account, db_obj.final_balance
            )
            type = NotificationTypes.WITHDRAW.value

        notifications_dao.send_notification(
            db,
            obj_in=CreateNotificationSerializer(
                channel=channel,
                phone=phone,
                message=message,
                type=type,
            ),
        )

    def get_user_balance(self, db: Session, *, account: str) -> float:
        latest_transaction = self.get_or_none(
            db, {"order_by": ["-created_at"], "account": account}
        )
        current_balance = 0.00
        if latest_transaction:
            current_balance = latest_transaction.final_balance

        return current_balance


transaction_dao = TransactionDao(Transactions)
