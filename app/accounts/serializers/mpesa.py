from typing import Optional
from pydantic import BaseModel

from app.core.helpers import _standardize_phone_to_required_format


class MpesaPaymentBaseSerializer(BaseModel):
    phone: str
    merchant_request_id: Optional[str]
    checkout_request_id: Optional[str]
    response_code: Optional[str]
    response_description: Optional[str]
    customer_message: Optional[str]

    _standardize_phone_to_required_format = _standardize_phone_to_required_format


class MpesaPaymentCreateSerializer(MpesaPaymentBaseSerializer):
    pass


class MpesaPaymentUpdateSerializer(MpesaPaymentBaseSerializer):
    pass
