from typing import Generator
import pytest

from app.db.session import SessionLocal, get_engine
from pytest_mock_resources import create_redis_fixture
from app.db.base import Base


redis = create_redis_fixture(scope="session")


@pytest.fixture(scope="session")
def db() -> Generator:
    # Create the db to be used in tests
    Base.metadata.create_all(bind=get_engine())
    with SessionLocal() as db:
        yield db

    Base.metadata.drop_all(bind=get_engine())
