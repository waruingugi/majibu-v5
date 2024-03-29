import requests
import json
from base64 import b64encode
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
import os

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509 import Certificate, load_pem_x509_certificate

from app.core.raw_logger import logger
from app.core.config import settings, redis
from app.core.helpers import (
    md5_hash,
    format_mpesa_result_params_to_dict,
    format_mpesa_receiver_details,
    format_b2c_mpesa_date_to_timestamp,
)
from app.accounts.constants import (
    MpesaAccountTypes,
    TransactionCashFlow,
    TransactionTypes,
    TransactionStatuses,
    TransactionServices,
    PAYBILL_DEPOSIT_DESCRIPTION,
)
from app.accounts.serializers.mpesa import (
    MpesaPaymentResultStkCallbackSerializer,
    MpesaPaymentCreateSerializer,
    MpesaDirectPaymentSerializer,
    WithdrawalCreateSerializer,
    WithdrawalResultBodySerializer,
)
from app.accounts.daos.mpesa import mpesa_payment_dao, withdrawal_dao
from app.accounts.daos.account import transaction_dao
from app.accounts.serializers.account import TransactionCreateSerializer
from app.users.models import User

from app.accounts.constants import B2CMpesaCommandIDs
from app.exceptions.custom import STKPushFailed, B2CPaymentFailed


def get_mpesa_access_token(
    MPESA_CONSUMER_KEY=settings.MPESA_CONSUMER_KEY,
    MPESA_SECRET=settings.MPESA_SECRET,
    IS_B2C: bool = False,
) -> str:
    """
    Get Mpesa Access Token.
    Requires the application secret and consumer key.
    We store the key in the server cache(Redis) for a period of 200
    seconds less than the one provided by Mpesa just to be safe.
    """
    logger.info("Retrieving M-Pesa token...")

    access_token = (
        redis.get("mpesa_b2c_access_token")
        if IS_B2C
        else redis.get("mpesa_access_token")
    )

    if not access_token:
        logger.info("Mpesa access token does not exist. Fetching from API...")
        url = settings.MPESA_TOKEN_URL
        auth = requests.auth.HTTPBasicAuth(MPESA_CONSUMER_KEY, MPESA_SECRET)

        req = requests.get(url, auth=auth, verify=True)
        res = req.json()

        access_token = res["access_token"]
        # The timeout set by mpesa is `3599` so we subtract 200 to be safe
        timeout = int(res["expires_in"]) - 200

        # Store the token in the cache for future requests
        (
            redis.set("mpesa_b2c_access_token", access_token, ex=timeout)
            if IS_B2C
            else redis.set("mpesa_access_token", access_token, ex=timeout)
        )

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
    logger.info(f"Initiate M-Pesa STKPush for Ksh {amount} to {phone_number}")

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
        logger.info(f"Sending M-Pesa STKPush for Ksh {amount} to {phone_number}")
        response = requests.post(api_url, json=data, headers=headers, verify=True)
        response_data = response.json()
        logger.info(f"Received M-Pesa STKPush response: {response_data}")

        if response_data["ResponseCode"] == "0":  # 0 means response is ok
            return response_data

    except Exception as e:
        logger.error(f"Initiating STKPush failed with response: {e}")
        raise STKPushFailed


def trigger_mpesa_stkpush_payment(amount: int, phone_number: str) -> Optional[Dict]:
    """Send Mpesa STK push."""
    logger.info(f"Trigerring M-Pesa STKPush for KES {amount} to {phone_number}")

    business_short_code = settings.MPESA_BUSINESS_SHORT_CODE
    party_b = settings.MPESA_BUSINESS_SHORT_CODE
    amount = amount
    account_reference = phone_number
    transaction_description = (
        f"Request for deposit of Ksh {amount} for account {phone_number} in Majibu."
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

        # Save the checkout response to db for future reference
        if data is not None:
            logger.info(
                f"Saving the checkout response {data['MerchantRequestID']} for {phone_number}"
            )
            with SessionLocal() as db:
                mpesa_payment_dao.create(
                    db,
                    obj_in=MpesaPaymentCreateSerializer(
                        phone_number=phone_number,
                        merchant_request_id=data["MerchantRequestID"],
                        checkout_request_id=data["CheckoutRequestID"],
                        response_code=data["ResponseCode"],
                        response_description=data["ResponseDescription"],
                        customer_message=data["CustomerMessage"],
                    ),
                )

        return data

    except STKPushFailed as e:
        logger.error(f"Trigering STKPush failed with exception: {e}")
        raise STKPushFailed


def process_mpesa_stk(
    db: Session, mpesa_response_in: MpesaPaymentResultStkCallbackSerializer
) -> None:
    """
    Process Mpesa STK payment from Callback or From Queue
    """
    logger.info("Initiating process_mpesa_stk task...")
    checkout_request_id = mpesa_response_in.CheckoutRequestID

    mpesa_payment = mpesa_payment_dao.get_or_none(
        db, checkout_request_id=checkout_request_id
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
        logger.warning(f"Received an unknown STKPush response: {mpesa_response_in}")


def process_mpesa_paybill_payment(
    db: Session, mpesa_response_in: MpesaDirectPaymentSerializer
) -> None:
    """Process direct payments to paybill"""
    logger.info("Processing M-Pesa paybill payment")
    description = PAYBILL_DEPOSIT_DESCRIPTION.format(
        mpesa_response_in.TransAmount, mpesa_response_in.MSISDN
    )

    transaction_in = TransactionCreateSerializer(
        account=mpesa_response_in.MSISDN,
        external_transaction_id=mpesa_response_in.TransID,
        cash_flow=TransactionCashFlow.INWARD.value,
        type=TransactionTypes.DEPOSIT.value,
        status=TransactionStatuses.SUCCESSFUL.value,
        service=TransactionServices.MPESA.value,
        description=description,
        amount=float(mpesa_response_in.TransAmount),
        external_response=json.dumps(mpesa_response_in.dict()),
    )

    transaction_dao.create(db, obj_in=transaction_in)


def get_mpesa_certificate() -> str:
    """Load the M-Pesa certification file that will be used for encryption"""
    logger.info("Retrieving M-Pesa certificate...")

    file_name = "ProductionCertificate.cer"
    current_path = os.path.dirname(__file__)
    cert_file_path = os.path.join(current_path, file_name)

    cert_file = open(cert_file_path, "r")
    cert_str = cert_file.read()
    cert_file.close()

    return cert_str


def get_initiator_security_credential() -> str:
    """Get cert and extract public key"""
    cert_str = get_mpesa_certificate()
    cert_obj: Certificate = load_pem_x509_certificate(str.encode(cert_str))
    public_key = cert_obj.public_key()

    # Encrypt key with public key and PKCS1v15 padding as recommended by safaricom
    byte_password = bytes(settings.MPESA_B2C_PASSWORD, "utf-8")
    ciphertext = public_key.encrypt(byte_password, padding=padding.PKCS1v15())  # type: ignore

    return b64encode(ciphertext).decode("utf-8")


def initiate_b2c_payment(
    *,
    amount: int,
    party_b: str,
    remarks: Optional[str] = "B2C API payment",
    occassion: Optional[str] = "B2C API payment",
    command_id: str = B2CMpesaCommandIDs.PROMOTIONPAYMENT.value,
) -> Dict | None:
    """Initiate an M-Pesa B2C payment"""
    access_token = get_mpesa_access_token(
        MPESA_CONSUMER_KEY=settings.MPESA_B2C_CONSUMER_KEY,
        MPESA_SECRET=settings.MPESA_B2C_SECRET,
        IS_B2C=True,
    )

    api_url = settings.MPESA_B2C_URL
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    try:
        payload = {
            "InitiatorName": settings.MPESA_B2C_INITIATOR_NAME,
            "SecurityCredential": get_initiator_security_credential(),
            "CommandID": command_id,
            "Amount": amount,
            "PartyA": settings.MPESA_B2C_SHORT_CODE,
            "PartyB": party_b,
            "Remarks": remarks,
            "QueueTimeOutURL": settings.MPESA_B2C_QUEUE_TIMEOUT_URL,
            "ResultURL": settings.MPESA_B2C_RESULT_URL,
            "Occassion": occassion,
        }
        response = requests.post(api_url, json=payload, headers=headers, verify=True)
        response_data = response.json()

        logger.info(f"Received B2C payment response: {response_data}")

        if response_data["ResponseCode"] == "0":  # 0 means response is ok
            return response_data

    except Exception as e:
        logger.error(f"An execption ocurred while initiating B2C payment: {e}")
        raise B2CPaymentFailed()


def process_b2c_payment(db: Session, *, user: User, amount: int):
    """Process an M-Pesa B2C payment request"""
    logger.info("Processing B2C payment")

    try:
        # Save hashed value that expires every 2 minutes.
        # That effectively only limits a user to 1 successful withdrawal
        # each 2 minutes
        hashed_withdrawal_request = md5_hash(f"{user.phone}:withdraw_request")
        redis.set(
            hashed_withdrawal_request, amount, ex=settings.WITHDRAWAL_BUFFER_PERIOD
        )
        phone = user.phone.replace("+", "")

        data = initiate_b2c_payment(amount=amount, party_b=phone)

        if data is not None:
            logger.info(
                f"Saving B2C response conversation Id: {data['ConversationID']}"
            )
            withdrawal_data = WithdrawalCreateSerializer(
                conversation_id=data["ConversationID"],
                originator_conversation_id=data["OriginatorConversationID"],
                response_code=data["ResponseCode"],
                response_description=data["ResponseDescription"],
            )

            withdrawal_dao.create(db, obj_in=withdrawal_data)

    except Exception as e:
        logger.error(f"An execption ocurred while processing B2C payment: {e}")
        raise B2CPaymentFailed()


def process_b2c_payment_result(
    db: Session, mpesa_b2c_result: WithdrawalResultBodySerializer
):
    """Process B2C payment"""
    logger.info("Processing B2C payment result.")
    try:
        withdrawal_request = withdrawal_dao.get_not_none(
            db, conversation_id=mpesa_b2c_result.ConversationID
        )

        result_parameters = mpesa_b2c_result.ResultParameters
        result_parameter = result_parameters.ResultParameter

        if (
            result_parameter is not None  # Confirms request origin was from Majibu
            and withdrawal_request.transaction_id
            is None  # Confirms a similar update has not been made
            and withdrawal_request.transaction_amount
            is None  # Double confirm similar update has not been made
        ):
            result_params = format_mpesa_result_params_to_dict(result_parameter)
            time_stamp = format_b2c_mpesa_date_to_timestamp(
                result_params["TransactionCompletedDateTime"]
            )
            phone, full_name = format_mpesa_receiver_details(
                result_params["ReceiverPartyPublicName"]
            )

            updated_withdrawal_request = {
                "result_code": mpesa_b2c_result.ResultCode,
                "result_description": mpesa_b2c_result.ResultDesc,
                "transaction_id": mpesa_b2c_result.TransactionID,
                "transaction_amount": result_params["TransactionAmount"],
                "working_account_available_funds": result_params[
                    "B2CWorkingAccountAvailableFunds"
                ],
                "utility_account_available_funds": result_params[
                    "B2CUtilityAccountAvailableFunds"
                ],
                "transaction_date": time_stamp,
                "phone_number": phone,
                "full_name": full_name,
                "charges_paid_account_available_funds": result_params[
                    "B2CChargesPaidAccountAvailableFunds"
                ],
                "external_response": json.dumps(mpesa_b2c_result.dict()),
            }

            withdrawal_dao.update(
                db, db_obj=withdrawal_request, obj_in=updated_withdrawal_request
            )

    except Exception as e:
        logger.warning(
            f"Error encountered while processing B2C response: {mpesa_b2c_result.dict()}"
        )
        logger.warning(f"An error occurred while processing B2C result: {e}")
        raise B2CPaymentFailed()
