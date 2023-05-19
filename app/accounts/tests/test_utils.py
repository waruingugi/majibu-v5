import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from typing import Callable
import pytest

from app.accounts.utils import (
    get_mpesa_access_token,
    initiate_mpesa_stkpush_payment,
    trigger_mpesa_stkpush_payment,
    initiate_b2c_payment,
    process_b2c_payment,
)
from app.core.config import redis, settings
from app.core.helpers import md5_hash
from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer

from app.accounts.daos.mpesa import withdrawal_dao
from app.accounts.constants import (
    TransactionCashFlow,
    TransactionServices,
    TransactionStatuses,
    TransactionTypes,
)
from app.accounts.constants import MpesaAccountTypes
from app.accounts.tests.test_data import (
    serialized_call_back,
    serialized_failed_call_back,
    mock_stk_push_response,
    mpesa_reference_no,
    serialized_paybill_deposit_response,
    sample_b2c_response,
    sample_failed_b2c_response,
)
from app.accounts.serializers.mpesa import MpesaPaymentCreateSerializer
from app.accounts.daos.mpesa import mpesa_payment_dao
from app.accounts.daos.account import transaction_dao
from app.accounts.utils import process_mpesa_stk, process_mpesa_paybill_payment
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
    assert float(transaction.final_balance) == float(1.0)


def test_process_mpesa_stk_fails_to_create_failed_stk_push_response(
    db: Session, delete_transcation_model_instances: Callable
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
    process_mpesa_stk(db, serialized_failed_call_back)

    transaction = transaction_dao.get_all(db)

    assert len(transaction) == 0


def test_process_mpesa_stk_fails_to_create_unknown_transaction_instance(
    db: Session, delete_previous_mpesa_payment_transactions: Callable
) -> None:
    process_mpesa_stk(db, serialized_call_back)
    mpesa_payments = mpesa_payment_dao.get_all(db)

    assert len(mpesa_payments) == 0


def test_process_mpesa_paybill_payment_creates_model_instance(
    db: Session, delete_transcation_model_instances: Callable
) -> None:
    process_mpesa_paybill_payment(db, serialized_paybill_deposit_response)
    transaction = transaction_dao.get(
        db, external_transaction_id=serialized_paybill_deposit_response.TransID
    )

    assert transaction is not None
    assert transaction.cash_flow == TransactionCashFlow.INWARD.value
    assert transaction.service == TransactionServices.MPESA.value
    assert transaction.status == TransactionStatuses.SUCCESSFUL.value
    assert transaction.type == TransactionTypes.PAYMENT.value
    assert float(transaction.amount) == float(
        serialized_paybill_deposit_response.TransAmount
    )
    assert float(transaction.final_balance) == float(
        serialized_paybill_deposit_response.TransAmount
    )


class TestMpesaB2CPayment(unittest.TestCase):
    mock_response = MagicMock()

    @patch("app.accounts.utils.get_mpesa_access_token")
    def test_initiate_b2c_payment_returns_correct_response(
        self, mock_get_mpesa_access_token
    ):
        mock_get_mpesa_access_token.return_value = "random_token"

        with patch("app.accounts.utils.requests") as mock_requests:
            self.mock_response.json.return_value = sample_b2c_response
            mock_requests.post.return_value = self.mock_response

            response = initiate_b2c_payment(
                amount=1,
                party_b=settings.SUPERUSER_PHONE,
            )

            assert response == self.mock_response.json()

    @patch("app.accounts.utils.get_mpesa_access_token")
    def test_initiate_b2c_payment_returns_none_if_error_in_response(
        self, mock_get_mpesa_access_token
    ):
        mock_get_mpesa_access_token.return_value = "random_token"

        with patch("app.accounts.utils.requests") as mock_requests:
            sample_b2c_response["ResponseCode"] = "1"
            self.mock_response.json.return_value = sample_b2c_response
            mock_requests.post.return_value = self.mock_response

            response = initiate_b2c_payment(
                amount=1,
                party_b=settings.SUPERUSER_PHONE,
            )

            assert response is None


def test_process_b2c_payment_creates_withdrawal_instance(
    db: Session, delete_withdrawal_model_instances: Callable
):
    with patch("app.accounts.utils.initiate_b2c_payment") as mock_initiate_b2c_payment:
        mock_initiate_b2c_payment.return_value = sample_b2c_response

        user = user_dao.get_or_create(
            db, obj_in=UserCreateSerializer(phone=settings.SUPERUSER_PHONE)
        )
        process_b2c_payment(db, user=user, amount=1)

        db_obj = withdrawal_dao.get(
            db, conversation_id=sample_b2c_response["ConversationID"]
        )
        cached_data = redis.get(md5_hash(f"{user.phone}:withdraw_request"))

        assert db_obj is not None
        assert cached_data is not None
        assert (
            db_obj.originator_conversation_id
            == sample_b2c_response["OriginatorConversationID"]
        )


def test_process_b2c_payment_fails_to_create_withdrawal_instance_if_response_is_none(
    db: Session, delete_withdrawal_model_instances: Callable
):
    with patch("app.accounts.utils.initiate_b2c_payment") as mock_initiate_b2c_payment:
        mock_initiate_b2c_payment.return_value = None

        user = user_dao.get_or_create(
            db, obj_in=UserCreateSerializer(phone=settings.SUPERUSER_PHONE)
        )
        process_b2c_payment(db, user=user, amount=1)

        db_obj = withdrawal_dao.get(
            db, conversation_id=sample_b2c_response["ConversationID"]
        )

        assert db_obj is None


def test_process_b2c_payment_raises_exception_on_error_response(
    db: Session, delete_withdrawal_model_instances: Callable
):
    with patch("app.accounts.utils.initiate_b2c_payment") as mock_initiate_b2c_payment:
        mock_initiate_b2c_payment.return_value = sample_failed_b2c_response

        user = user_dao.get_or_create(
            db, obj_in=UserCreateSerializer(phone=settings.SUPERUSER_PHONE)
        )
        with pytest.raises(Exception):
            process_b2c_payment(db, user=user, amount=1)

            db_obj = withdrawal_dao.get(
                db, conversation_id=sample_b2c_response["ConversationID"]
            )

            assert db_obj is None
