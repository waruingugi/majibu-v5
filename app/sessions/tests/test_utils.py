from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from typing import Callable
import random
import pytest

from app.core.config import settings
from app.users.daos.user import user_dao
from app.commons.constants import Categories

from app.sessions.utils import (
    GetAvailableSession,
    create_session,
)
from app.sessions.daos.session import session_dao
from app.accounts.daos.account import transaction_dao
from app.accounts.constants import (
    TransactionServices,
    TransactionCashFlow,
)

from app.quiz.daos.quiz import result_dao
from app.quiz.serializers.quiz import ResultCreateSerializer
from app.exceptions.custom import SessionInQueue, InsufficientUserBalance


def test_get_available_sessions_fails_if_active_results(
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
    create_session_model_instances: Callable,
    delete_result_model_instances: Callable,
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
    assert sorted(sessions) == sorted(played_sessions)


def test_query_is_active_result_sessions_returns_correct_list(
    db: Session,
    create_super_user_instance: Callable,
    # create_user_model_instances: Callable,
    create_result_instances_to_be_paired: Callable,
    create_session_model_instances: Callable,
    mock_user_has_sufficient_balance: Callable,
    delete_duo_session_model_instances: Callable,
    delete_result_model_instances: Callable,
) -> None:
    """Assert class function returns correct list of result sessions
    that the user can be paired to."""
    sessions = session_dao.get_all(db)

    # Create random super user results
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    played_result_sessions = []

    # Use a random no between 1 and 9 so that not all created sessions are used up
    # This allows the tested function to find a difference between played_result_sessions and
    # available sessions. The difference will be the pending duo sessions that the
    # user can play
    for session in sessions[6:]:
        result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
        result_dao.create(db, obj_in=result_in)

        played_result_sessions.append(session.id)

    # Set up other class functions that are called before the specific tested function
    get_available_session = GetAvailableSession(db, user)

    # Pick a random category
    get_available_session.category = random.choice(Categories.list_())
    get_available_session.played_session_ids = (
        get_available_session.query_sessions_played()
    )

    # Call the specific function to be tested
    available_sessions = get_available_session.query_is_active_result_sessions()

    for sesion_id in played_result_sessions:
        assert sesion_id not in available_sessions


def test_query_available_sessions_returns_correct_list(
    db: Session,
    create_super_user_instance: Callable,
    create_session_model_instances: Callable,
    mock_user_has_sufficient_balance: Callable,
    delete_result_model_instances: Callable,
):
    """Assert query_available_sessions returns correct list ids from the Sessions model
    that the user has not played"""
    sessions = session_dao.get_all(db)
    no_of_sessions = len(sessions)

    random_no = random.randint(1, no_of_sessions)
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    played_sessions = []

    for session in sessions[0:random_no]:
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
    available_sessions = get_available_session.query_available_sessions()

    for sesion_id in played_sessions:
        assert sesion_id not in available_sessions


def test_create_session_deducts_from_user_wallet_balance(
    db: Session,
    create_super_user_instance: Callable,
    create_session_model_instances: Callable,
    mock_user_has_sufficient_balance: Callable,
    delete_result_model_instances: Callable,
    delete_transcation_model_instances: Callable,
):
    """
    - Test that the function create_session creates a result model instance
    - Test that the function create_session deducts from the users wallet the correct values
    """
    session = session_dao.get_not_none(db)
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)

    result_id = create_session(db, user=user, session_id=session.id)

    transaction_obj = transaction_dao.get_not_none(
        db, service=TransactionServices.SESSION.value
    )
    result = result_dao.get_not_none(db)

    assert result_id is not None
    assert result.session_id == session.id
    assert transaction_obj.amount == settings.SESSION_AMOUNT
    assert transaction_obj.cash_flow == TransactionCashFlow.OUTWARD.value
    assert transaction_obj.service == TransactionServices.SESSION.value


def test_create_session_fails_for_insufficient_wallet_balance(
    db: Session,
    create_super_user_instance: Callable,
    create_session_model_instances: Callable,
    delete_result_model_instances: Callable,
    delete_transcation_model_instances: Callable,
):
    """Test that the function raises an exception if user has insufficient balance"""
    session = session_dao.get_not_none(db)
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)

    with pytest.raises(InsufficientUserBalance):
        create_session(db, user=user, session_id=session.id)
