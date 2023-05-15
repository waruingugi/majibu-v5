from sqlalchemy.orm import Session
import json
from typing import Callable

from app.accounts.tests.test_data import (
    sample_transaction_instance_info,
    mock_stk_push_response,
    serialized_call_back,
)
from app.accounts.serializers.account import TransactionCreateSerializer
from app.accounts.serializers.mpesa import MpesaPaymentCreateSerializer
from app.accounts.utils import process_mpesa_stk
from app.accounts.daos.account import transaction_dao
from app.accounts.daos.mpesa import mpesa_payment_dao
from app.core.config import settings


def test_create_transaction_instance_succesfully(
    db: Session, delete_previous_transcations: Callable
) -> None:
    """Test created transaction instance has correct default values"""
    obj_in = TransactionCreateSerializer(**sample_transaction_instance_info)
    db_obj = transaction_dao.create(db, obj_in=obj_in)

    assert db_obj.account == sample_transaction_instance_info["account"]
    assert db_obj.charge == 1.00
    assert db_obj.initial_balance == 0.00
    assert db_obj.final_balance == 1.00


def test_new_transaction_shows_correct_final_balance(
    db: Session, delete_previous_transcations: Callable
) -> None:
    obj_in = TransactionCreateSerializer(**sample_transaction_instance_info)
    transaction_dao.create(db, obj_in=obj_in)

    # Then create a new transaction
    sample_transaction_instance_info["external_transaction_id"] = "NLJ7RT61SB"
    sample_transaction_instance_info["amount"] = 9.0

    db_obj = transaction_dao.create(
        db, obj_in=TransactionCreateSerializer(**sample_transaction_instance_info)
    )

    assert db_obj.final_balance == 10.00
    assert db_obj.initial_balance == 1.00


def test_mpesa_payment_is_created_successfully(
    db: Session, delete_previous_mpesa_payment_transactions: Callable
):
    data = mock_stk_push_response

    db_obj = mpesa_payment_dao.create(
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

    assert db_obj is not None
    assert db_obj.amount is None
    assert db_obj.receipt_number is None
    assert db_obj.phone_number == settings.SUPERUSER_PHONE


def test_mpesa_payment_is_updated_successfully(
    db: Session, delete_previous_mpesa_payment_transactions: Callable
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
    process_mpesa_stk(db, serialized_call_back)
    db_obj = mpesa_payment_dao.get_not_none(
        db, merchant_request_id=data["MerchantRequestID"]
    )

    assert db_obj.receipt_number is not None
    assert db_obj.external_response == json.dumps(serialized_call_back.dict())
    assert db_obj.amount > 0.00
