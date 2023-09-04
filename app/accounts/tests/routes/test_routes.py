from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session
from typing import Callable

from app.accounts.daos.mpesa import mpesa_payment_dao
from app.accounts.constants import MPESA_WHITE_LISTED_IPS
from app.accounts.serializers.mpesa import MpesaPaymentCreateSerializer
from app.accounts.tests.test_data import (
    mock_stk_push_response,
    mock_stk_push_result,
    sample_paybill_deposit_response,
    sample_successful_b2c_result,
)

from app.errors.custom import ErrorCodes
from app.core.config import settings, redis
from app.core.helpers import md5_hash


def test_post_deposit_creates_model_instance(
    db: Session, client: TestClient, mocker: MockerFixture
) -> None:
    mocker.patch(
        "app.accounts.utils.initiate_mpesa_stkpush_payment",
        return_value=mock_stk_push_response,
    )

    client.post("/accounts/deposit/", data={"amount": "1"})

    db_obj = mpesa_payment_dao.get(db, merchant_request_id="29115-34620561-1")

    assert db_obj is not None
    assert db_obj.merchant_request_id == "29115-34620561-1"


def test_post_callback_fails_with_http_exception(
    db: Session, client: TestClient, mocker: MockerFixture
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
    response = client.post("/accounts/payments/callback/", json=mock_stk_push_result)

    assert "Forbidden" in response.context["server_errors"]


def test_post_callback_accepts_white_listed_ips(
    db: Session, client: TestClient, mocker: MockerFixture
) -> None:
    mock_client = mocker.patch("fastapi.Request.client")
    mock_client.host = MPESA_WHITE_LISTED_IPS[0]

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
    response = client.post("/accounts/payments/callback/", json=mock_stk_push_result)

    assert hasattr(response, "context") is False


def test_post_confirmation_accepts_white_listed_ips(
    client: TestClient,
    mocker: MockerFixture,
    delete_transcation_model_instances: Callable,
) -> None:
    mock_client = mocker.patch("fastapi.Request.client")
    mock_client.host = MPESA_WHITE_LISTED_IPS[0]

    response = client.post(
        "/accounts/payments/confirmation/", json=sample_paybill_deposit_response
    )

    assert hasattr(response, "context") is False


def test_post_confirmation_fails_with_http_exception(client: TestClient) -> None:
    response = client.post(
        "/accounts/payments/confirmation/", json=sample_paybill_deposit_response
    )

    assert "Forbidden" in response.context["server_errors"]


def test_post_withdraw_fails_on_insufficient_balance(
    client: TestClient, mocker: MockerFixture
) -> None:
    mocker.patch("app.accounts.routes.account.process_b2c_payment", return_value=None)
    response = client.post("/accounts/withdraw/", data={"amount": "70000"})

    field_error = "You do not have sufficient balance to withdraw ksh70000"
    assert field_error in response.context["field_errors"]


def test_post_withdraw_fails_if_previous_request_exists(
    client: TestClient, mocker: MockerFixture
) -> None:
    redis.flushall()  # Clear all values from redis
    mocker.patch("app.accounts.routes.account.process_b2c_payment", return_value=None)
    mocker.patch(  # Inflate user's balance by ksh50
        "app.accounts.routes.account.transaction_dao.get_user_balance", return_value=50
    )

    # Set a previous request in redis
    hashed_withdrawal_request = md5_hash(f"{settings.SUPERUSER_PHONE}:withdraw_request")
    timeout = 60 * 2  # 2 minutes
    redis.set(hashed_withdrawal_request, 15, ex=timeout)

    response = client.post("/accounts/withdraw/", data={"amount": "1"})

    field_error = ErrorCodes.SIMILAR_WITHDRAWAL_REQUEST.value
    assert field_error in response.context["field_errors"]


def test_post_withdraw_succeeds_in_calling_process_b2c_payment(
    client: TestClient, mocker: MockerFixture
) -> None:
    redis.flushall()  # Clear all values from redis
    mock_process_b2c_payment = mocker.patch(
        "app.accounts.routes.account.process_b2c_payment", return_value=None
    )
    mocker.patch(  # Inflate user's balance by ksh50
        "app.accounts.routes.account.transaction_dao.get_user_balance", return_value=50
    )
    response = client.post("/accounts/withdraw/", data={"amount": "1"})

    assert ("field_errors" in response.context) is False
    assert mock_process_b2c_payment.call_count == 1


def test_post_withdrawal_result_successfully_calls_process_b2c_payment_result_func(
    client: TestClient, mocker: MockerFixture
) -> None:
    mock_client = mocker.patch("fastapi.Request.client")
    mock_client.host = MPESA_WHITE_LISTED_IPS[0]

    mock_process_b2c_payment_result = mocker.patch(
        "app.accounts.routes.account.process_b2c_payment_result", return_value=None
    )
    client.post("/accounts/payments/result/", json=sample_successful_b2c_result)

    assert mock_process_b2c_payment_result.call_count == 1


def test_post_withdrawal_result_successfully_fails_with_http_exception(
    client: TestClient,
) -> None:
    response = client.post(
        "/accounts/payments/result/", json=sample_successful_b2c_result
    )

    assert "Forbidden" in response.context["server_errors"]
