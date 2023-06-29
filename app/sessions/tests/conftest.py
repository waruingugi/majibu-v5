import pytest
import random
from typing import Callable
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture

from app.commons.utils import generate_uuid
from app.commons.constants import Categories
from app.core.config import settings
from app.sessions.daos.session import session_dao, duo_session_dao
from app.sessions.serializers.session import SessionCreateSerializer
from app.quiz.daos.quiz import result_dao


@pytest.fixture
def delete_session_model_instances(db: Session) -> None:
    """Delete all existing rows in Results model"""
    sessions = session_dao.get_all(db)
    for session in sessions:
        session_dao.remove(db, id=session.id)


@pytest.fixture
def create_sesion_model_instances(
    db: Session, delete_session_model_instances: Callable
) -> None:
    """Create several session model instances"""
    for i in range(10):
        question_ids = [generate_uuid() for i in range(settings.QUESTIONS_IN_SESSION)]

        session_dao.create(
            db,
            obj_in=SessionCreateSerializer(
                category=random.choice(Categories.list_()), questions=question_ids
            ),
        )


@pytest.fixture
def delete_result_model_instances(db: Session) -> None:
    """Delete all existing rows in Results model"""
    results = result_dao.get_all(db)
    for result in results:
        result_dao.remove(db, id=result.id)


@pytest.fixture
def delete_duo_session_model_instances(db: Session) -> None:
    """Delete previously existing rows in DuoSession model"""
    existing_duo_sessions = duo_session_dao.get_all(db)
    for duo_session in existing_duo_sessions:
        duo_session_dao.remove(db, id=duo_session.id)


@pytest.fixture
def mock_user_has_sufficient_balance(db: Session, mocker: MockerFixture) -> None:
    """Mock has_sufficient_balance function to return true in utils"""
    mocker.patch(
        "app.sessions.utils.has_sufficient_balance",
        return_value=True,
    )
