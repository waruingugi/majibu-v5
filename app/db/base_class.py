from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import DateTime, String
from sqlalchemy.orm import mapped_column
from sqlalchemy_utils import get_columns
from typing import Dict

import uuid
from datetime import datetime


def get_current_datetime() -> datetime:
    return datetime.now()


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    __abstract__ = True
    __name__: str

    # All tables inheriting from Base class contains this columns
    id = mapped_column(String, primary_key=True, default=generate_uuid)
    created_at = mapped_column(DateTime, default=get_current_datetime, nullable=False)
    updated_at = mapped_column(
        DateTime, default=None, onupdate=get_current_datetime, nullable=True
    )

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    @classmethod
    def get_model_columns(cls) -> Dict[str, str]:
        return get_columns(cls).keys()
