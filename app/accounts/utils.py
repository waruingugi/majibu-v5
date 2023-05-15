import requests
import json
from base64 import b64encode
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.raw_logger import logger
from app.core.config import settings, redis
from app.accounts.constants import MpesaAccountTypes
from app.accounts.serializers.mpesa import MpesaPaymentResultStkCallbackSerializer
from app.accounts.daos.mpesa import mpesa_payment_dao
from app.exceptions.custom import STKPushFailed


def get_mpesa_access_token() -> str:
    """
    Get Mpesa Access Token.
    Requires the application secret and consumer key.
    We store the key in the server cache(Redis) for a period of 200
    seconds less than the one provided by Mpesa just to be safe.
    """
    logger.info("Retrieving M-Pesa token...")

    access_token = redis.get("mpesa_access_token")

    if access_token:
        access_token = (
            str(access_token, "utf-8")
            if isinstance(access_token, bytes)
            else access_token
        )

    if not access_token:
        url = settings.MPESA_TOKEN_URL
        auth = requests.auth.HTTPBasicAuth(
            settings.MPESA_CONSUMER_KEY, settings.MPESA_SECRET
        )

        req = requests.get(url, auth=auth, verify=True)
        res = req.json()

        access_token = res["access_token"]
        # The timeout set by mpesa is `3599` so we subtract 200 to be safe
        timeout = int(res["expires_in"]) - 200

        # Store the token in the cache for future requests
        redis.set("mpesa_access_token", access_token, ex=timeout)

    return access_token


def initiate_mpesa_stkpush_payment(
    phone_number: str,
    amount: int,
    business_short_code: str,
    party_b: str,
    passkey: str,
    transaction_type: str,
    callback_url: str,
    reference: str,
    description: str,
) -> Dict | None:
    """Trigger STKPush"""
    logger.info(f"Initiate M-Pesa STKPush for KES {amount} to {phone_number}")

    access_token = get_mpesa_access_token()
    phone_number = str(phone_number).replace("+", "")
    timestamp = datetime.now().strftime(settings.MPESA_DATETIME_FORMAT)

    password = b64encode(
        bytes(f"{business_short_code}{passkey}{timestamp}", "utf-8")
    ).decode("utf-8")

    api_url = settings.MPESA_STKPUSH_URL
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    try:
        data = {
            "BusinessShortCode": business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": transaction_type,
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": party_b,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": reference,
            "TransactionDesc": description,
        }
        response = requests.post(api_url, json=data, headers=headers, verify=True)
        response_data = response.json()

        if response_data["ResponseCode"] == "0":  # 0 means response is ok
            return response_data

    except Exception as e:
        logger.warning(f"Initiating STKPush failed with response: {e}")
        raise STKPushFailed


def trigger_mpesa_stkpush_payment(amount: int, phone_number: str) -> Optional[Dict]:
    """Send Mpesa STK push."""
    logger.info(f"Trigerring M-Pesa STKPush for KES {amount} to {phone_number}")

    business_short_code = settings.MPESA_BUSINESS_SHORT_CODE
    party_b = settings.MPESA_BUSINESS_SHORT_CODE
    amount = amount
    account_reference = phone_number
    transaction_description = (
        f"Request for deposit of KES {amount} for account {phone_number} in Majibu."
    )
    try:
        passkey = settings.MPESA_PASS_KEY
        data = initiate_mpesa_stkpush_payment(
            phone_number=phone_number,
            amount=int(amount),
            business_short_code=business_short_code,
            passkey=passkey,
            party_b=party_b,
            transaction_type=MpesaAccountTypes.PAYBILL.value,
            callback_url=settings.MPESA_CALLBACK_URL,
            description=transaction_description,
            reference=account_reference,
        )

        return data

    except STKPushFailed as e:
        logger.warning(f"Trigering STKPush failed with exception: {e}")
        raise STKPushFailed


def process_mpesa_stk(
    db: Session, mpesa_response_in: MpesaPaymentResultStkCallbackSerializer
) -> None:
    """
    Process Mpesa STK payment from Callback or From Queue
    """
    checkout_request_id = mpesa_response_in.CheckoutRequestID

    mpesa_payment = mpesa_payment_dao.get_or_none(
        db, {"checkout_request_id": checkout_request_id}
    )

    if mpesa_payment:
        logger.info(
            f"Received response for previous STKPush {mpesa_payment.checkout_request_id}"
        )

        updated_mpesa_payment = {
            "result_code": mpesa_response_in.ResultCode,
            "result_description": mpesa_response_in.ResultDesc,
            "external_response": json.dumps(mpesa_response_in.dict()),
        }

        if mpesa_response_in.CallbackMetadata:
            for item in mpesa_response_in.CallbackMetadata.Item:
                if item.Name == "Amount":
                    updated_mpesa_payment["amount"] = item.Value
                if item.Name == "MpesaReceiptNumber":
                    updated_mpesa_payment["receipt_number"] = item.Value
                if item.Name == "Balance":
                    updated_mpesa_payment["balance"] = item.Value
                if item.Name == "TransactionDate":
                    updated_mpesa_payment["transaction_date"] = datetime.strptime(
                        str(item.Value), settings.MPESA_DATETIME_FORMAT
                    )
                if item.Name == "PhoneNumber":
                    updated_mpesa_payment["phone_number"] = "+" + str(item.Value)

        mpesa_payment_dao.update(db, db_obj=mpesa_payment, obj_in=updated_mpesa_payment)

        logger.info(f"Received mpesa payment: {updated_mpesa_payment}")

    else:
        logger.info("Received an unknown STKPush response: {mpesa_response_in}")
