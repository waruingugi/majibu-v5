from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from app.accounts.daos.mpesa import mpesa_payment_dao
from app.accounts.constants import MPESA_WHITE_LISTED_IPS
from app.accounts.serializers.mpesa import MpesaPaymentCreateSerializer
from app.accounts.tests.test_data import (
    mock_stk_push_response,
    mock_stk_push_result,
    sample_paybill_deposit_response,
)
from app.core.config import settings


def test_post_deposit_creates_model_instance(
    db: Session, client: TestClient, mocker: MockerFixture
):
    mocker.patch(
        "app.accounts.routes.account.trigger_mpesa_stkpush_payment",
        return_value=mock_stk_push_response,
    )

    client.post("/accounts/deposit/", data={"amount": "1"})

    db_obj = mpesa_payment_dao.get(db, merchant_request_id="29115-34620561-1")

    assert db_obj is not None
    assert db_obj.merchant_request_id == "29115-34620561-1"


def test_post_callback_fails_with_http_exception(
    db: Session, client: TestClient, mocker: MockerFixture
):
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
):
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
    client: TestClient, mocker: MockerFixture
):
    mock_client = mocker.patch("fastapi.Request.client")
    mock_client.host = MPESA_WHITE_LISTED_IPS[0]

    response = client.post(
        "/accounts/payments/confirmation/", json=sample_paybill_deposit_response
    )

    assert hasattr(response, "context") is False


def test_post_confirmation_fails_with_http_exception(
    client: TestClient, mocker: MockerFixture
):
    response = client.post(
        "/accounts/payments/confirmation/", json=sample_paybill_deposit_response
    )

    assert "Forbidden" in response.context["server_errors"]
