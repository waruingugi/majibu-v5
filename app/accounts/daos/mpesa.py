from sqlalchemy.orm import Session

from app.db.dao import CRUDDao, ChangedObjState
from app.accounts.models import MpesaPayments
from app.accounts.daos.account import transaction_dao
from app.accounts.serializers.mpesa import (
    MpesaPaymentCreateSerializer,
    MpesaPaymentUpdateSerializer,
)
from app.accounts.serializers.account import TransactionCreateSerializer
from app.accounts.constants import (
    TransactionCashFlow,
    TransactionTypes,
    TransactionServices,
    TransactionStatuses,
)


class MpesaPaymentDao(
    CRUDDao[MpesaPayments, MpesaPaymentCreateSerializer, MpesaPaymentUpdateSerializer]
):
    def on_post_update(
        self, db: Session, db_obj: MpesaPayments, changed: ChangedObjState
    ) -> None:
        result_code = changed["result_code"]["after"]
        account = changed["phone_number"]["after"]
        external_transaction_id = changed["receipt_number"]["after"]
        amount = changed["amount"]["after"]
        description = (
            f"Deposit of KES {amount} for account {account} using M-Pesa STKPush."
        )

        if (
            result_code == 0
            and external_transaction_id  # If Mpesa transacation is successful
            is not None
        ):
            transaction_dao.create(
                db,
                obj_in=TransactionCreateSerializer(
                    account=account,
                    external_transaction_id=external_transaction_id,
                    cash_flow=TransactionCashFlow.INWARD.value,
                    type=TransactionTypes.PAYMENT.value,
                    status=TransactionStatuses.SUCCESSFUL.value,
                    service=TransactionServices.MPESA.value,
                    description=description,
                    fee=0.0,  # No charge for deposits
                    tax=0.0,  # No tax for deposits
                ),
            )


mpesa_payment_dao = MpesaPaymentDao(MpesaPayments)
