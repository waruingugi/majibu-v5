from typing import Optional, Union, List
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


class MpesaPaymentResultItemSerializer(BaseModel):
    Name: str
    Value: Optional[Union[int, str]]


class MpesaPaymentResultCallbackMetadataSerializer(BaseModel):
    Item: List[MpesaPaymentResultItemSerializer]


class MpesaPaymentResultStkCallbackSerializer(BaseModel):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: Optional[MpesaPaymentResultCallbackMetadataSerializer]


class MpesaPaymentResultBodySerializer(BaseModel):
    stkCallback: MpesaPaymentResultStkCallbackSerializer


class MpesaPaymentResultSerializer(BaseModel):
    Body: MpesaPaymentResultBodySerializer
