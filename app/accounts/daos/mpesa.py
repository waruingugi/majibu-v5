from sqlalchemy.orm import Session

from app.db.dao import CRUDDao, ChangedObjState
from app.accounts.models import MpesaPayments, Withdrawals
from app.accounts.daos.account import transaction_dao
from app.accounts.serializers.mpesa import (
    MpesaPaymentCreateSerializer,
    MpesaPaymentUpdateSerializer,
    WithdrawalCreateSerializer,
    WithdrawalUpdateSerializer,
)
from app.accounts.serializers.account import TransactionCreateSerializer
from app.accounts.constants import (
    TransactionCashFlow,
    TransactionTypes,
    TransactionServices,
    TransactionStatuses,
)
from app.accounts.constants import STKPUSH_DEPOSIT_DESCRPTION


class MpesaPaymentDao(
    CRUDDao[MpesaPayments, MpesaPaymentCreateSerializer, MpesaPaymentUpdateSerializer]
):
    def on_post_update(
        self, db: Session, db_obj: MpesaPayments, changed: ChangedObjState
    ) -> None:

        if (
            db_obj.result_code == 0  # If Mpesa transacation is successful
            and db_obj.receipt_number is not None  # Must have a valid M-Pesa Reference
        ):
            description = STKPUSH_DEPOSIT_DESCRPTION.format(
                db_obj.amount, db_obj.phone_number
            )

            transaction_dao.create(
                db,
                obj_in=TransactionCreateSerializer(
                    account=db_obj.phone_number,
                    external_transaction_id=db_obj.receipt_number,
                    cash_flow=TransactionCashFlow.INWARD.value,
                    type=TransactionTypes.PAYMENT.value,
                    status=TransactionStatuses.SUCCESSFUL.value,
                    service=TransactionServices.MPESA.value,
                    description=description,
                    amount=db_obj.amount,
                    fee=0.0,  # No charge for deposits
                    tax=0.0,  # No tax for deposits
                    external_response=db_obj.external_response,
                ),
            )


mpesa_payment_dao = MpesaPaymentDao(MpesaPayments)


class WithdrawalDao(
    CRUDDao[Withdrawals, WithdrawalCreateSerializer, WithdrawalUpdateSerializer]
):
    pass


withdrawal_dao = WithdrawalDao(Withdrawals)
