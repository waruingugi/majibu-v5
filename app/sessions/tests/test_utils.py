from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from typing import Callable
import random
import pytest

from app.core.config import settings
from app.commons.constants import Categories
from app.sessions.utils import QueryAvailableSession
from app.sessions.daos.session import session_dao
from app.users.daos.user import user_dao
from app.quiz.daos.quiz import result_dao
from app.quiz.serializers.quiz import ResultCreateSerializer
from app.exceptions.custom import SessionInQueue


def test_query_available_sessions_fails_if_active_results(
    db: Session,
    mocker: MockerFixture,
    create_super_user_instance: Callable,
    create_session_instance: Callable,
    delete_result_model_instances: Callable,
) -> None:
    """Test the class fails if there is  an active session/active result"""
    mocker.patch(
        "app.sessions.utils.has_sufficient_balance",
        return_value=True,
    )
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    session = session_dao.get_not_none(db, category=Categories.BIBLE.value)

    result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
    result_dao.create(db, obj_in=result_in)

    with pytest.raises(SessionInQueue):
        query_available_session = QueryAvailableSession(db, user)
        _ = query_available_session(category=Categories.FOOTBALL.value)


def test_query_sessions_played_returns_empty_list(
    db: Session,
    mocker: MockerFixture,
    create_super_user_instance: Callable,
    create_session_instance: Callable,
    delete_result_model_instances: Callable,
    mock_user_has_sufficient_balance: Callable,
) -> None:
    """Test class function returns empty list when user hasn't played any session"""
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    query_available_session = QueryAvailableSession(db, user)
    sessions = query_available_session.query_sessions_played()

    assert len(sessions) == 0


def test_query_sessions_played_returns_correct_list(
    db: Session,
    mocker: MockerFixture,
    create_super_user_instance: Callable,
    create_user_model_instances: Callable,
    create_sesion_model_instances: Callable,
    mock_user_has_sufficient_balance: Callable,
) -> None:
    """Test that the class function query_sessions_played returns correct list of session ids"""
    sessions = session_dao.get_all(db)

    # Create random user results
    for session in sessions[4:]:
        users = user_dao.search(
            db, search_filter={"phone__neq": settings.SUPERUSER_PHONE}
        )
        user = random.choice(users)
        result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
        result_dao.create(db, obj_in=result_in)

    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    played_sessions = []

    # Create super user results
    for session in sessions[:3]:
        result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
        result_dao.create(db, obj_in=result_in)
        played_sessions.append(session.id)

    query_available_session = QueryAvailableSession(db, user)
    sessions = query_available_session.query_sessions_played()

    # Assert that result of the function is a correct list of sessions played by super user
    assert sessions == played_sessions
