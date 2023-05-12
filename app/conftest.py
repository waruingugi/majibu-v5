from typing import Generator
import pytest

from fastapi.testclient import TestClient
from app.db.session import SessionLocal, get_engine
from app.db.base import Base
from app.main import app

from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer
from app.core.config import settings
from app.core.deps import get_current_active_user


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
