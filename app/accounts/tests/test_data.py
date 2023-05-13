from app.core.config import settings
import json


mock_stk_push_response = {
    "phone": settings.SUPERUSER_PHONE,
    "MerchantRequestID": "29115-34620561-1",
    "CheckoutRequestID": "ws_CO_191220191020363925",
    "ResponseCode": "0",
    "ResponseDescription": "Success. Request accepted for processing",
    "CustomerMessage": "Success. Request accepted for processing",
}


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
                    {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                    {"Name": "TransactionDate", "Value": 20191219102115},
                    {"Name": "PhoneNumber", "Value": 254708374149},
                ]
            },
        }
    }
}

sample_transaction_instance_info = {
    "account": settings.SUPERUSER_PHONE,
    "external_transaction_id": "NLJ7RT61SV",
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
