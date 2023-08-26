from datetime import datetime, timedelta
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session
from typing import Callable
import random
import pytest

from app.core.utils import PairUsers
from app.core.config import settings
from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer
from app.commons.constants import Categories

from app.sessions.utils import (
    view_session_history,
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


def test_view_session_history_returns_correct_value_for_pending_session(
    db: Session,
    create_super_user_instance: Callable,
    create_session_instance: Callable,
    delete_duo_session_model_instances: Callable,
) -> None:
    """Assert function returns correct values for a result that has been played but has
    not been paired yet."""
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    session = session_dao.get_not_none(db, category=Categories.BIBLE.value)

    result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
    result = result_dao.create(db, obj_in=result_in)

    session_history = view_session_history(db, user)
    result_history = session_history[0]

    assert result_history["status"] == "PENDING"
    assert result_history["category"] == result.category

    assert result_history["party_a"]["score"] == round(result.score, 2)


def test_view_session_history_returns_empty_list_for_no_results_played(
    db: Session,
    create_super_user_instance: Callable,
    delete_result_model_instances: Callable,
    delete_duo_session_model_instances: Callable,
) -> None:
    """Assert function returns empty list if user has not played any session before."""
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    session_history = view_session_history(db, user)

    assert len(session_history) == 0


def test_view_session_history_returns_correct_value_for_a_partially_refunded_session(
    db: Session,
    mocker: MockerFixture,
    delete_duo_session_model_instances: Callable,
    create_result_instances_to_be_paired: Callable,
) -> None:
    """Assert function returns correct value for a partially refunded session"""
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        minutes=settings.SESSION_DURATION
    )
    pair_users = PairUsers()
    result_node = pair_users.results_queue[0]

    # Set result_node score to 0.0 so that it's partially refunded
    result_node.score = 0.0
    pair_users.match_players()

    user = user_dao.get_not_none(db, id=result_node.user_id)
    session_history = view_session_history(db, user)
    result_history = session_history[0]

    assert result_history["status"] == "PARTIALLY_REFUNDED"
    assert result_history["category"] == result_node.category
    assert "party_a" in result_history


def test_view_session_history_returns_correct_value_for_a_refunded_session(
    db: Session,
    mocker: MockerFixture,
    delete_duo_session_model_instances: Callable,
    create_result_instances_to_be_paired: Callable,
) -> None:
    """Assert function returns correct value for a refunded session"""
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        minutes=settings.SESSION_DURATION
    )

    result_objs = result_dao.get_all(db)
    party_a_result = result_objs[0]
    # Set an outrageous high score so that no partner is found
    result_dao.update(db, db_obj=party_a_result, obj_in={"score": 100})

    pair_users = PairUsers()
    pair_users.match_players()

    user = user_dao.get_not_none(db, id=party_a_result.user_id)
    session_history = view_session_history(db, user)
    result_history = session_history[0]

    assert result_history["status"] == "REFUNDED"
    assert result_history["category"] == party_a_result.category
    assert result_history["party_a"]["score"] == 100.00


def test_view_session_history_returns_correct_value_for_a_paired_session(
    db: Session,
    mocker: MockerFixture,
    delete_duo_session_model_instances: Callable,
    create_result_instances_to_be_paired: Callable,
) -> None:
    """Assert function returns correct values for paired results"""
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        minutes=settings.SESSION_DURATION
    )

    # Get two users and modify their scores to be super close
    party_b_user = user_dao.get_or_create(
        db, UserCreateSerializer(phone="+254764845040")
    )

    """I noticed that if you don't use the earliest created result as party_a,
    other results may pair with part_b causing this test to fail"""
    result_objs = result_dao.search(db, {"order_by": ["created_at"]})
    party_a_result = result_objs[0]

    # Ensure their session_id is same and their scores are super close
    party_b_result = result_dao.create(
        db,
        obj_in=ResultCreateSerializer(
            user_id=party_b_user.id, session_id=party_a_result.session_id
        ),
    )
    result_dao.update(
        db,
        db_obj=party_a_result,  # type: ignore
        obj_in={  # type: ignore
            "score": 75.112  # System accuracy is only upto 7 digits: settings.SESSION_RESULT_DECIMAL_PLACES
        },
    )
    result_dao.update(
        db,
        db_obj=party_b_result,
        obj_in={
            "score": 75.111  # System accuracy is only upto 7 digits: settings.SESSION_RESULT_DECIMAL_PLACES
        },
    )

    pair_users = PairUsers()
    pair_users.match_players()

    party_a_user = user_dao.get_not_none(db, id=party_a_result.user_id)
    party_a_session_history = view_session_history(db, party_a_user)
    party_a_result_history = party_a_session_history[0]

    party_b_user = user_dao.get_not_none(db, id=party_b_result.user_id)
    party_b_session_history = view_session_history(db, party_b_user)
    party_b_result_history = party_b_session_history[0]

    assert party_a_result_history["status"] == "WON"
    assert party_a_result_history["category"] == party_a_result.category
    assert party_a_result_history["party_a"]["score"] == 75.11

    assert party_b_result_history["status"] == "LOST"
    assert party_b_result_history["category"] == party_b_result.category
    assert party_b_result_history["party_b"]["score"] == 75.11
