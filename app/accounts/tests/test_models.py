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
