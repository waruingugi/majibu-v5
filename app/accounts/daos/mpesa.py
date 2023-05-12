# from sqlalchemy.orm import Session

from app.db.dao import CRUDDao
from app.accounts.models import MpesaPayments
from app.accounts.serializers.mpesa import (
    MpesaPaymentCreateSerializer,
    MpesaPaymentUpdateSerializer,
)


class MpesaPaymentDao(
    CRUDDao[MpesaPayments, MpesaPaymentCreateSerializer, MpesaPaymentUpdateSerializer]
):
    pass


mpesa_payment_dao = MpesaPaymentDao(MpesaPayments)
