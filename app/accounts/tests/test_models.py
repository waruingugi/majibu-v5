from sqlalchemy.orm import Session

from app.accounts.tests.test_data import sample_transaction_instance_info
from app.accounts.serializers.account import TransactionCreateSerializer
from app.accounts.daos.account import transaction_dao


def test_create_transaction_instance_succesfully(db: Session) -> None:
    """Test created transaction instance has correct default values"""
    obj_in = TransactionCreateSerializer(**sample_transaction_instance_info)
    db_obj = transaction_dao.create(db, obj_in=obj_in)

    assert db_obj.account == sample_transaction_instance_info["account"]
    assert db_obj.charge == 1.00
    assert db_obj.initial_balance == 0.00
    assert db_obj.final_balance == 1.00


def test_new_transaction_shows_correct_final_balance(db: Session) -> None:
    # First delete previously existing rows
    previous_transactions = transaction_dao.get_all(
        db, account=sample_transaction_instance_info["account"]
    )
    for transaction in previous_transactions:
        transaction_dao.remove(db, id=transaction.id)

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
