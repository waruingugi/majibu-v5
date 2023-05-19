from fastapi.testclient import TestClient

from app.db.session import SessionLocal, get_engine
from app.db.base import Base
from app.main import app

from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer
from app.core.config import settings
from app.core.deps import get_current_active_user
from app.accounts.daos.mpesa import mpesa_payment_dao
from app.accounts.daos.account import transaction_dao


from sqlalchemy.orm import Session
from typing import Generator
import pytest


@pytest.fixture
def delete_transcation_model_instances(db: Session) -> None:
    # Delete previously existing rows in Transactions model
    previous_transactions = transaction_dao.get_all(db)
    for transaction in previous_transactions:
        transaction_dao.remove(db, id=transaction.id)


@pytest.fixture
def delete_previous_mpesa_payment_transactions(db: Session) -> None:
    # Delete previously existing rows in Mpesa Payments model
    previous_transactions = mpesa_payment_dao.get_all(db)
    for transaction in previous_transactions:
        mpesa_payment_dao.remove(db, id=transaction.id)


@pytest.fixture(scope="session")
def db() -> Generator:
    # Create the db to be used in tests
    Base.metadata.create_all(bind=get_engine())
    with SessionLocal() as db:
        yield db

    Base.metadata.drop_all(bind=get_engine())


def mock_create_user():
    with SessionLocal() as db:
        user = user_dao.get_or_create(
            db, obj_in=UserCreateSerializer(phone=settings.SUPERUSER_PHONE)
        )
        return user


@pytest.fixture(scope="session")
def client():
    Base.metadata.create_all(bind=get_engine())

    with TestClient(app) as client:
        # using dependency overrides to mock the function get_current_active_user
        app.dependency_overrides[get_current_active_user] = mock_create_user

        yield client
