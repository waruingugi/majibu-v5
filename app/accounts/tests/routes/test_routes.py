from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from app.accounts.daos.mpesa import mpesa_payment_dao
from app.core.config import settings


def test_post_deposit_creates_model_instance(
    db: Session, client: TestClient, mocker: MockerFixture
):
    mock_stk_push_response = {
        "phone_number": settings.SUPERUSER_PHONE,
        "MerchantRequestID": "29115-34620561-1",
        "CheckoutRequestID": "ws_CO_191220191020363925",
        "ResponseCode": "0",
        "ResponseDescription": "Success. Request accepted for processing",
        "CustomerMessage": "Success. Request accepted for processing",
    }
    mocker.patch(
        "app.accounts.routes.account.trigger_mpesa_stkpush_payment",
        return_value=mock_stk_push_response,
    )

    client.post("/accounts/deposit/", data={"amount": "1"})

    db_obj = mpesa_payment_dao.get(db, merchant_request_id="29115-34620561-1")

    assert db_obj is not None
    assert db_obj.merchant_request_id == "29115-34620561-1"
