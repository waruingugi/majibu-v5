from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
import json
from typing import Callable

from app.accounts.tests.test_data import (
    sample_positive_transaction_instance_info,
    sample_negative_transaction_instance_info,
    sample_b2c_response,
    mock_stk_push_response,
    serialized_call_back,
)
from app.accounts.serializers.account import TransactionCreateSerializer
from app.accounts.serializers.mpesa import (
    MpesaPaymentCreateSerializer,
    WithdrawalCreateSerializer,
)
from app.accounts.utils import process_mpesa_stk
from app.accounts.daos.account import transaction_dao
from app.accounts.daos.mpesa import mpesa_payment_dao, withdrawal_dao
from app.core.config import settings


def test_create_positive_transaction_instance_succesfully(
    db: Session, mocker: MockerFixture, delete_transcation_model_instances: Callable
) -> None:
    """Test created transaction instance has correct default values"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    obj_in = TransactionCreateSerializer(**sample_positive_transaction_instance_info)
    db_obj = transaction_dao.create(db, obj_in=obj_in)

    assert db_obj.account == sample_positive_transaction_instance_info["account"]
    assert db_obj.charge == 1.00
    assert db_obj.initial_balance == 0.00
    assert db_obj.final_balance == 1.00


def test_create_negative_transaction_instance_succesfully(
    db: Session, mocker: MockerFixture, delete_transcation_model_instances: Callable
) -> None:
    """Test created withdrawal transaction instance has correct default values"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    data = sample_positive_transaction_instance_info.copy()
    data["amount"] = 100
    obj_in = TransactionCreateSerializer(**data)
    transaction_dao.create(db, obj_in=obj_in)

    obj_in = TransactionCreateSerializer(**sample_negative_transaction_instance_info)
    db_obj = transaction_dao.create(db, obj_in=obj_in)

    assert db_obj.account == sample_negative_transaction_instance_info["account"]
    assert db_obj.charge == 36.00
    assert db_obj.initial_balance == 100.00
    assert db_obj.final_balance == 64.00


def test_new_transaction_shows_correct_final_balance(
    db: Session, mocker: MockerFixture, delete_transcation_model_instances: Callable
) -> None:
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    obj_in = TransactionCreateSerializer(**sample_positive_transaction_instance_info)
    transaction_dao.create(db, obj_in=obj_in)

    # Then create a new transaction
    data = sample_positive_transaction_instance_info.copy()
    data["external_transaction_id"] = "NLJ7RT61SB"
    data["amount"] = 9.0

    db_obj = transaction_dao.create(db, obj_in=TransactionCreateSerializer(**data))

    assert db_obj.final_balance == 10.00
    assert db_obj.initial_balance == 1.00


def test_transaction_dao_shows_correct_user_balance(
    db: Session, mocker: MockerFixture, delete_transcation_model_instances: Callable
) -> None:
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    sample_positive_transaction_instance_info["amount"] = 9.55

    transaction_dao.create(
        db,
        obj_in=TransactionCreateSerializer(**sample_positive_transaction_instance_info),
    )
    user_balance = transaction_dao.get_user_balance(
        db, account=sample_positive_transaction_instance_info["account"]
    )

    assert float(user_balance) == 9.55


def test_mpesa_payment_is_created_successfully(
    db: Session,
    delete_transcation_model_instances: Callable,
    delete_previous_mpesa_payment_transactions: Callable,
) -> None:
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
    db: Session,
    delete_transcation_model_instances: Callable,
    delete_previous_mpesa_payment_transactions: Callable,
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
    db_obj = mpesa_payment_dao.get_not_none(
        db, merchant_request_id=data["MerchantRequestID"]
    )

    assert db_obj.receipt_number is not None
    assert db_obj.external_response == json.dumps(serialized_call_back.dict())
    assert db_obj.amount > 0.00


def test_create_withdrawal_instance_succesfully(db: Session) -> None:
    """Test created withdrawal instance has correct default values"""
    data = sample_b2c_response
    db_obj = withdrawal_dao.create(
        db,
        obj_in=WithdrawalCreateSerializer(
            conversation_id=data["ConversationID"],
            originator_conversation_id=data["OriginatorConversationID"],
            response_code=data["ResponseCode"],
            response_description=data["ResponseDescription"],
        ),
    )

    assert db_obj.conversation_id == sample_b2c_response["ConversationID"]
    assert (
        db_obj.originator_conversation_id
        == sample_b2c_response["OriginatorConversationID"]
    )
