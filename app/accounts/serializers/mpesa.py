from typing import Optional, Union, List
from pydantic import BaseModel, validator

from app.core.helpers import standardize_phone_to_required_format


class MpesaPaymentBaseSerializer(BaseModel):
    phone_number: Optional[str]
    merchant_request_id: Optional[str]
    checkout_request_id: Optional[str]
    response_code: Optional[str]
    response_description: Optional[str]
    customer_message: Optional[str]

    _standardize_phone_to_required_format = validator(
        "phone_number", pre=True, allow_reuse=True
    )(standardize_phone_to_required_format)


class MpesaPaymentCreateSerializer(MpesaPaymentBaseSerializer):
    pass


class MpesaPaymentUpdateSerializer(MpesaPaymentBaseSerializer):
    pass


class MpesaPaymentResultItemSerializer(BaseModel):
    Name: str
    Value: Optional[Union[int, str]] = ""


class MpesaPaymentResultCallbackMetadataSerializer(BaseModel):
    Item: List[MpesaPaymentResultItemSerializer]


class MpesaPaymentResultStkCallbackSerializer(BaseModel):
    MerchantRequestID: str
    CheckoutRequestID: str
    ResultCode: int
    ResultDesc: str
    CallbackMetadata: Optional[MpesaPaymentResultCallbackMetadataSerializer] = None


class MpesaPaymentResultBodySerializer(BaseModel):
    stkCallback: MpesaPaymentResultStkCallbackSerializer


class MpesaPaymentResultSerializer(BaseModel):
    Body: MpesaPaymentResultBodySerializer


class MpesaDirectPaymentSerializer(BaseModel):
    TransactionType: str
    TransID: str
    TransTime: str
    TransAmount: str
    BusinessShortCode: str
    BillRefNumber: Optional[str] = ""
    InvoiceNumber: Optional[str] = ""
    OrgAccountBalance: Optional[str] = ""
    ThirdPartyTransID: Optional[str] = ""
    MSISDN: str
    FirstName: Optional[str] = ""
    MiddleName: Optional[str] = ""
    LastName: Optional[str] = ""

    _standardize_phone_to_required_format = validator(
        "MSISDN", pre=True, allow_reuse=True
    )(standardize_phone_to_required_format)


class WithdrawalBaseSerializer(BaseModel):
    ConversationID: str
    OriginatorConversationID: str
    ResponseCode: str
    ResponseDescription: str


class WithdawalCreateSerializer(WithdrawalBaseSerializer):
    pass


class KeyValueDict(BaseModel):
    Key: str
    Value: str


class WithdrawalReferenceItemSerializer(BaseModel):
    ReferenceItem: KeyValueDict


class WithdrawalResultBodyParaments(BaseModel):
    ResultParameter: List[KeyValueDict]


class WithdrawalResultBodySerializer(BaseModel):
    ResultType: int
    ResultCode: int
    ResultDesc: str
    OriginatorConversationID: str
    ConversationID: str
    TransactionID: str
    ResultParameters: Optional[WithdrawalResultBodyParaments] = None
    ReferenceData: WithdrawalReferenceItemSerializer


class WithdrawalResultSerializer(BaseModel):
    Result: WithdrawalResultBodySerializer
