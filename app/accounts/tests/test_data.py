from app.core.config import settings
from app.accounts.serializers.mpesa import (
    MpesaPaymentResultCallbackMetadataSerializer,
    MpesaPaymentResultStkCallbackSerializer,
    MpesaPaymentResultBodySerializer,
    MpesaDirectPaymentSerializer,
)
import json


# M-Pesa Reference Number
mpesa_reference_no = "NLJ7RT61SV"

# M-Pesa STKPush response
mock_stk_push_response = {
    "phone": settings.SUPERUSER_PHONE,
    "MerchantRequestID": "29115-34620561-1",
    "CheckoutRequestID": "ws_CO_191220191020363925",
    "ResponseCode": "0",
    "ResponseDescription": "Success. Request accepted for processing",
    "CustomerMessage": "Success. Request accepted for processing",
}

# M-Pesa STKPush result
mock_stk_push_result = {
    "Body": {
        "stkCallback": {
            "MerchantRequestID": "29115-34620561-1",
            "CheckoutRequestID": "ws_CO_191220191020363925",
            "ResultCode": 0,
            "ResultDesc": "The service request is processed successfully.",
            "CallbackMetadata": {
                "Item": [
                    {"Name": "Amount", "Value": 1.00},
                    {"Name": "MpesaReceiptNumber", "Value": mpesa_reference_no},
                    {"Name": "TransactionDate", "Value": 20191219102115},
                    {"Name": "PhoneNumber", "Value": 254708374149},
                ]
            },
        }
    }
}

# Transaction instance to be saved in Transaction model
sample_transaction_instance_info = {
    "account": settings.SUPERUSER_PHONE,
    "external_transaction_id": mpesa_reference_no,
    "cash_flow": "INWARD",
    "type": "PAYMENT",
    "status": "SUCCESSFUL",
    "service": "MPESA",
    "description": "",
    "amount": 1.0,
    "fee": 0.0,
    "tax": 0.0,
    "external_response": json.dumps({}),
}

# Sample pf failed STKPush response
sample_failed_stk_push_response = {
    "Body": {
        "stkCallback": {
            "MerchantRequestID": "29115-34620561-1",
            "CheckoutRequestID": "ws_CO_191220191020363925",
            "ResultCode": 1032,
            "ResultDesc": "Request canceled by user.",
        }
    }
}

# Serialized M-Pesa STKPush result
serialized_call_back_metadata = MpesaPaymentResultCallbackMetadataSerializer(
    **mock_stk_push_result["Body"]["stkCallback"]["CallbackMetadata"]
)

serialized_call_back = MpesaPaymentResultStkCallbackSerializer(
    CallbackMetadata=serialized_call_back_metadata,
    MerchantRequestID=mock_stk_push_result["Body"]["stkCallback"]["MerchantRequestID"],
    CheckoutRequestID=mock_stk_push_result["Body"]["stkCallback"]["CheckoutRequestID"],
    ResultCode=mock_stk_push_result["Body"]["stkCallback"]["ResultCode"],
    ResultDesc=mock_stk_push_result["Body"]["stkCallback"]["ResultDesc"],
)

serialized_result_body = MpesaPaymentResultBodySerializer(
    stkCallback=serialized_call_back
)

serialized_failed_call_back = MpesaPaymentResultStkCallbackSerializer(
    MerchantRequestID=sample_failed_stk_push_response["Body"]["stkCallback"][
        "MerchantRequestID"
    ],
    CheckoutRequestID=sample_failed_stk_push_response["Body"]["stkCallback"][
        "CheckoutRequestID"
    ],
    ResultCode=sample_failed_stk_push_response["Body"]["stkCallback"]["ResultCode"],
    ResultDesc=sample_failed_stk_push_response["Body"]["stkCallback"]["ResultDesc"],
)


# M-Pesa Paybill Response

sample_paybill_deposit_response = {
    "TransactionType": "Pay Bill",
    "TransID": "RKTQDM7W6S",
    "TransTime": "20191122063845",
    "TransAmount": "10",
    "BusinessShortCode": settings.MPESA_BUSINESS_SHORT_CODE,
    "BillRefNumber": settings.SUPERUSER_PHONE,
    "InvoiceNumber": "",
    "OrgAccountBalance": "35.00",
    "ThirdPartyTransID": "",
    "MSISDN": settings.SUPERUSER_PHONE,
    "FirstName": "WARUI",
    "MiddleName": "NGUGI",
    "LastName": "NGUGI",
}
serialized_paybill_deposit_response = MpesaDirectPaymentSerializer(
    **sample_paybill_deposit_response
)
