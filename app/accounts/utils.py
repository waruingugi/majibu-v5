import hashlib
import hmac
import base64
import requests
import json
from base64 import b64encode
from typing import Optional, Dict
from datetime import datetime

from app.core.raw_logger import logger
from app.core.config import settings, redis
from app.accounts.constants import MpesaAccountTypes
from app.exceptions.custom import StkPushFailed


def generate_transaction_code():
    """Generate unique transaction codes"""
    logger.info("Generating unique transaction code")

    # Create uniqueness based on date
    now = datetime.now()
    msg = f"{now.month}{now.day}{now.hour}{now.minute}{now.second}{now.microsecond}".encode(
        "utf-8"
    )
    secret_key = bytes(settings.SECRET_KEY, "utf-8")
    signature = hmac.new(secret_key, msg=msg, digestmod=hashlib.sha256).digest()

    transaction_id = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    transaction_id = transaction_id.upper()  # Convert transaction_id to uppercase
    transaction_code = "".join([c for c in transaction_id if c.isalnum()])

    return f"M{transaction_code[:8]}"


def get_mpesa_access_token() -> str:
    """
    Get Mpesa Access Token.
    Requires the application secret and consumer key.
    We store the key in the server cache(Redis) for a period of 200
    seconds less than the one provided by Mpesa just to be safe.
    """
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
    reference: Optional[str],
    description: Optional[str],
) -> Dict:
    """Trigger STKPush"""
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
    if response.ok:
        return json.loads(response.text)
    else:
        logger.warning(f"STKPush failed with response: {response.text}")
        raise StkPushFailed


def trigger_mpesa_stkpush_payment(amount: int, phone_number: str) -> Optional[Dict]:
    """Send Mpesa STK push."""
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

    except StkPushFailed as e:
        logger.warning(f"STKPush failed with exception: {e}")
        raise StkPushFailed
