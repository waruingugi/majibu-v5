from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from typing import Callable
import random
import pytest

from app.core.config import settings
from app.commons.constants import Categories

from app.sessions.utils import GetAvailableSession
from app.sessions.daos.session import session_dao
from app.sessions.serializers.session import DuoSessionCreateSerializer

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
        get_available_session = GetAvailableSession(db, user)
        _ = get_available_session(category=Categories.FOOTBALL.value)


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
    get_available_session = GetAvailableSession(db, user)
    sessions = get_available_session.query_sessions_played()

    assert len(sessions) == 0


def test_query_sessions_played_returns_correct_list(
    db: Session,
    create_super_user_instance: Callable,
    create_user_model_instances: Callable,
    create_sesion_model_instances: Callable,
    mock_user_has_sufficient_balance: Callable,
) -> None:
    """Test that the class function query_sessions_played returns correct list of session ids"""
    sessions = session_dao.get_all(db)
    users = user_dao.search(db, search_filter={"phone__neq": settings.SUPERUSER_PHONE})

    # Create random user results
    for session in sessions[4:]:
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

    get_available_session = GetAvailableSession(db, user)
    sessions = get_available_session.query_sessions_played()

    # Assert that result of the function is a correct list of sessions played by super user
    assert sessions == played_sessions


def test_query_available_pending_duo_sessions_returns_correct_list(
    db: Session,
    create_super_user_instance: Callable,
    create_user_model_instances: Callable,
    create_sesion_model_instances: Callable,
    mock_user_has_sufficient_balance: Callable,
    delete_duo_session_model_instances: Callable,
    delete_result_model_instances: Callable,
) -> None:
    """Assert class function returns correct list pending DuoSession model instances
    that the user can be paired to."""
    sessions = session_dao.get_all(db)
    users = user_dao.search(db, search_filter={"phone__neq": settings.SUPERUSER_PHONE})

    # Create multiple random duo sessions
    # Use a random no between 1 and 9 so that not all created sessions are used up
    for i in range(7):
        party_a = random.choice(users)
        session = random.choice(sessions)  # Created sessions

        DuoSessionCreateSerializer(party_a=party_a.id, session_id=session.id)

    # Create random super user results
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    played_sessions = []

    # Use a random no between 1 and 9 so that not all created sessions are used up
    # This allows the tested function to find a difference between played_sessions and
    # available sessions. The difference will be the pending duo sessions that the
    # user can play
    for session in sessions[6:]:
        result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
        result_dao.create(db, obj_in=result_in)

        played_sessions.append(session.id)

    # Set up other class functions that are called before the specific tested function
    get_available_session = GetAvailableSession(db, user)

    # Pick a random category
    get_available_session.category = random.choice(Categories.list_())
    get_available_session.played_session_ids = (
        get_available_session.query_sessions_played()
    )

    # Call the specific function to be tested
    available_sessions = get_available_session.query_available_pending_duo_sessions()

    for sesion_id in played_sessions:
        assert sesion_id not in available_sessions
