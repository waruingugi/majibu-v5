import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from typing import Callable

from app.accounts.utils import (
    get_mpesa_access_token,
    initiate_mpesa_stkpush_payment,
    trigger_mpesa_stkpush_payment,
)
from app.accounts.constants import (
    TransactionCashFlow,
    TransactionServices,
    TransactionStatuses,
    TransactionTypes,
)
from app.core.config import redis, settings
from app.accounts.constants import MpesaAccountTypes
from app.accounts.tests.test_data import (
    serialized_call_back,
    mock_stk_push_response,
    mpesa_reference_no,
)
from app.accounts.serializers.mpesa import MpesaPaymentCreateSerializer
from app.accounts.daos.mpesa import mpesa_payment_dao
from app.accounts.daos.account import transaction_dao
from app.accounts.utils import process_mpesa_stk
from app.exceptions.custom import STKPushFailed


class TestMpesaSTKPush(unittest.TestCase):
    mock_response = MagicMock()

    @classmethod
    def setUp(cls):
        redis.flushall()  # Flush all values from redis

    @classmethod
    def tearDown(cls):
        redis.flushall()  # Flush all values from redis

    @patch("app.accounts.utils.requests")
    def test_get_mpesa_access_token(self, mock_requests) -> None:
        expected_access_token = "fake_access_token"
        self.mock_response.json.return_value = {
            "access_token": expected_access_token,
            "expires_in": "3599",
        }
        mock_requests.get.return_value = self.mock_response

        access_token = get_mpesa_access_token()
        assert access_token == expected_access_token

    @patch("app.accounts.utils.requests")
    def test_get_mpesa_access_token_is_set_in_redis(self, mock_requests) -> None:
        expected_access_token = "fake_access_token"
        self.mock_response.json.return_value = {
            "access_token": expected_access_token,
            "expires_in": "3599",
        }
        mock_requests.get.return_value = self.mock_response

        get_mpesa_access_token()  # Call first time
        access_token = get_mpesa_access_token()  # Second call
        assert access_token == expected_access_token
        assert mock_requests.get.call_count == 1

    @patch("app.accounts.utils.get_mpesa_access_token")
    def test_initiate_mpesa_stkpush_payment_returns_successful_response(
        self, mock_get_mpesa_access_token
    ) -> None:
        mock_get_mpesa_access_token.return_value = "fake_access_token"

        with patch("app.accounts.utils.requests") as mock_requests:
            self.mock_response.json.return_value = {
                "MerchantRequestID": "29115-34620561-1",
                "CheckoutRequestID": "ws_CO_191220191020363925",
                "ResponseCode": "0",
                "ResponseDescription": "Success. Request accepted for processing",
                "CustomerMessage": "Success. Request accepted for processing",
            }
            mock_requests.post.return_value = self.mock_response

            response = initiate_mpesa_stkpush_payment(
                phone_number=settings.SUPERUSER_PHONE,
                amount=1,
                business_short_code=settings.MPESA_BUSINESS_SHORT_CODE,
                party_b=settings.MPESA_BUSINESS_SHORT_CODE,
                passkey=settings.MPESA_PASS_KEY,
                transaction_type=MpesaAccountTypes.PAYBILL.value,
                callback_url=settings.MPESA_CALLBACK_URL,
                reference=settings.SUPERUSER_PHONE,
                description="",
            )

            assert response == self.mock_response.json()

    @patch("app.accounts.utils.get_mpesa_access_token")
    @patch("app.accounts.utils.requests")
    def test_initiate_mpesa_stkpush_payment_raises_exception(
        self, mock_get_mpesa_access_token, mock_requests
    ) -> None:
        mock_get_mpesa_access_token.return_value = "fake_access_token"

        with self.assertRaises(Exception):
            mock_requests.side_effect = STKPushFailed

            initiate_mpesa_stkpush_payment(
                phone_number=settings.SUPERUSER_PHONE,
                amount=1,
                business_short_code=settings.MPESA_BUSINESS_SHORT_CODE,
                party_b=settings.MPESA_BUSINESS_SHORT_CODE,
                passkey=settings.MPESA_PASS_KEY,
                transaction_type=MpesaAccountTypes.PAYBILL.value,
                callback_url=settings.MPESA_CALLBACK_URL,
                reference=settings.SUPERUSER_PHONE,
                description="",
            )

    @patch("app.accounts.utils.initiate_mpesa_stkpush_payment")
    def test_trigger_mpesa_stkpush_payment(
        self, mock_initiate_mpesa_stkpush_payment
    ) -> None:
        mock_initiate_mpesa_stkpush_payment.return_value = {
            "MerchantRequestID": "29115-34620561-1",
            "CheckoutRequestID": "ws_CO_191220191020363925",
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing",
            "CustomerMessage": "Success. Request accepted for processing",
        }
        response = trigger_mpesa_stkpush_payment(
            amount=1, phone_number=settings.SUPERUSER_PHONE
        )
        assert response == mock_initiate_mpesa_stkpush_payment.return_value


def test_process_mpesa_stk_successfully_creates_transaction_instance(
    db: Session,
) -> None:
    data = mock_stk_push_response

    mpesa_payment_dao.create(
        db,
        MpesaPaymentCreateSerializer(
            phone_number=settings.SUPERUSER_PHONE,
            merchant_request_id=data["MerchantRequestID"],
            checkout_request_id=data["CheckoutRequestID"],
            response_code=data["ResponseCode"],
            response_description=data["ResponseDescription"],
            customer_message=data["CustomerMessage"],
        ),
    )
    process_mpesa_stk(db, serialized_call_back)

    transaction = transaction_dao.get(db, external_transaction_id=mpesa_reference_no)

    assert transaction is not None
    assert transaction.cash_flow == TransactionCashFlow.INWARD.value
    assert transaction.service == TransactionServices.MPESA.value
    assert transaction.status == TransactionStatuses.SUCCESSFUL.value
    assert transaction.type == TransactionTypes.PAYMENT.value


def test_process_mpesa_stk_fails_to_create_unknown_transaction_instance(
    db: Session, delete_previous_mpesa_payment_transactions: Callable
) -> None:
    process_mpesa_stk(db, serialized_call_back)
    mpesa_payments = mpesa_payment_dao.get_all(db)

    assert len(mpesa_payments) == 0
