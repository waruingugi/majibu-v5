from typing import Generator
import pytest

from app.db.session import SessionLocal, get_engine
from app.db.base_class import Base


@pytest.fixture(scope="function")
def db() -> Generator:
    # Create the db to be used in tests
    Base.metadata.create_all(bind=get_engine())
    with SessionLocal() as db:
        yield db
