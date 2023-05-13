from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from app.accounts.daos.mpesa import mpesa_payment_dao
from app.accounts.constants import MPESA_WHITE_LISTED_IPS
from app.accounts.serializers.mpesa import MpesaPaymentCreateSerializer
from app.accounts.tests.test_data import mock_stk_push_response, mock_stk_push_result
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


def test_post_callback(db: Session, client: TestClient, mocker: MockerFixture):
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
    client.post("/accounts/payments/callback/", json=mock_stk_push_result)
