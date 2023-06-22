from sqlalchemy.orm import Session
from typing import Callable
import pytest

from app.commons.constants import Categories
from app.sessions.daos.session import session_dao, duo_session_dao
from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer
from app.sessions.serializers.session import (
    SessionCreateSerializer,
    DuoSessionCreateSerializer,
    DuoSessionUpdateSerializer,
)
from app.core.config import settings


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


def test_session_has_required_no_of_questions(db: Session) -> None:
    """Test fails if session has invalid number of questions"""
    with pytest.raises(Exception):
        data_in = SessionCreateSerializer(
            category=Categories.FOOTBALL.value,
            questions=[
                "1RBVS",
                "2WEBAN",
                "3FGTK",
                "4FBNA",
                "5QWNC",
                "6TNAV",
            ],  # In reality, these are unique UUID
        )
        session_dao.create(db, obj_in=data_in)


def test_create_duo_session_instance(
    db: Session,
    create_session_instance: Callable,
    create_user_instance: Callable,
) -> None:
    """Test DuoSession can be created in model"""
    session = session_dao.get_not_none(db)
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    data_in = DuoSessionCreateSerializer(
        party_a=user.id, session_id=session.id, amount=settings.SESSION_AMOUNT
    )
    duo_session = duo_session_dao.create(db, obj_in=data_in)

    assert duo_session.party_a == user.id
    assert duo_session.party_b is None

    assert duo_session.session_id == session.id
    assert duo_session.amount == settings.SESSION_AMOUNT


def test_update_duo_session_instance(
    db: Session,
    create_session_instance: Callable,
    create_user_instance: Callable,
    delete_duo_session_model_instances: Callable,
):
    """Test DuoSession can be updated in model"""
    session = session_dao.get_not_none(db)
    party_a = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)

    party_b = user_dao.get_or_create(
        db, obj_in=UserCreateSerializer(phone="+254764845040")
    )

    # Create DuoSession
    data_in = DuoSessionCreateSerializer(
        party_a=party_a.id, session_id=session.id, amount=settings.SESSION_AMOUNT
    )
    duo_session = duo_session_dao.create(db, obj_in=data_in)

    # Update the DuoSession
    updated_duo_session = duo_session_dao.update(
        db,
        db_obj=duo_session,
        obj_in=DuoSessionUpdateSerializer(
            party_b=party_b.id, status=False, winner_id=party_b.id
        ),
    )

    assert updated_duo_session.party_a == party_a.id
    assert updated_duo_session.party_b == party_b.id

    assert updated_duo_session.winner_id == party_b.id


def test_updated_duo_session_fails_if_user_is_the_same(
    db: Session,
    create_session_instance: Callable,
    create_user_instance: Callable,
    delete_duo_session_model_instances: Callable,
):
    """Test DuoSession fails to pair the same user to themselves"""
    session = session_dao.get_not_none(db)
    party_a = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)

    # Create DuoSession
    data_in = DuoSessionCreateSerializer(
        party_a=party_a.id, session_id=session.id, amount=settings.SESSION_AMOUNT
    )
    duo_session = duo_session_dao.create(db, obj_in=data_in)

    with pytest.raises(Exception):
        # Update the DuoSession
        duo_session_dao.update(
            db,
            db_obj=duo_session,
            obj_in=DuoSessionUpdateSerializer(
                party_b=party_a.id, status=False, winner_id=party_a.id
            ),
        )
