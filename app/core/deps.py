from typing import Generator
from app.db.session import SessionLocal


def get_db() -> Generator:
    with SessionLocal() as db:
        yield db
