from typing import Generator
import pytest

from fastapi.testclient import TestClient
from app.db.session import SessionLocal, get_engine
from app.db.base import Base
from app.main import app


@pytest.fixture(scope="session")
def db() -> Generator:
    # Create the db to be used in tests
    Base.metadata.create_all(bind=get_engine())
    with SessionLocal() as db:
        yield db

    Base.metadata.drop_all(bind=get_engine())


@pytest.fixture(scope="session")
def client():
    return TestClient(app)
