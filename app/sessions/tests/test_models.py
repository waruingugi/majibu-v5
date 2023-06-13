from sqlalchemy.orm import Session

from app.commons.constants import Categories
from app.sessions.daos.session import session_dao
from app.sessions.serializers.session import (
    SessionCreateSerializer,
)
import pytest


def test_create_session_instance(db: Session) -> None:
    """Test session can be created in model"""
    data_in = SessionCreateSerializer(
        category=Categories.FOOTBALL.value,
        questions=["1", "2", "3", "4", "5"],  # In reality, these are unique UUID
    )
    session = session_dao.create(db, obj_in=data_in)

    assert session.category == Categories.FOOTBALL.value
    assert "1" in session.questions
    assert "4" in session.questions


def test_session_creation_enforces_question_uniqueness(db: Session) -> None:
    """Test session can not have a question in another session"""
    data_in = SessionCreateSerializer(
        category=Categories.FOOTBALL.value,
        questions=[
            "1ERJD",
            "GHH2",
            "DHY3",
            "4FTHD",
            "BVF5",
        ],  # In reality, these are unique UUID
    )
    session_dao.create(db, obj_in=data_in)

    with pytest.raises(Exception):
        data_in = SessionCreateSerializer(
            category=Categories.FOOTBALL.value,
            questions=[
                "1ERJD",
                "DRS2",
                "TYB3",
                "RT54",
                "FGE3",
            ],  # In reality, these are unique UUID
        )
        session_dao.create(db, obj_in=data_in)
