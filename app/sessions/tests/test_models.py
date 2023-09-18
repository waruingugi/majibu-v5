from pytest_mock import MockerFixture
from sqlalchemy.orm import Session
from typing import Callable
import pytest
import json

from app.core.config import settings
from app.commons.constants import Categories
from app.exceptions.custom import DuoSessionFailedOnCreate
from app.accounts.daos.account import transaction_dao

from app.sessions.daos.session import (
    session_dao,
    duo_session_dao,
    user_session_stats_dao,
    pool_session_stats_dao,
)
from app.sessions.serializers.session import (
    SessionCreateSerializer,
    DuoSessionCreateSerializer,
    UserSessionStatsCreateSerializer,
    UserSessionStatsUpdateSerializer,
    PoolSessionStatsCreateSerializer,
    PoolCategoryStatistics,
)
from app.sessions.constants import DuoSessionStatuses

from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer


# def test_create_pool_session_stats_instance(db: Session) -> None:
#     """Assert PoolSessionStats instance can be created in the model"""
#     pool_session_stats = pool_session_stats_dao.create(
#         db,
#         obj_in=PoolSessionStatsCreateSerializer(
#             total_players=2,
#             average_score=72,
#             mean_pairwise_difference=2,
#             exp_weighted_moving_average=71,
#         ),
#     )

#     assert pool_session_stats.total_players == 2
#     assert pool_session_stats.average_score == 72
#     assert pool_session_stats.threshold == settings.PAIRING_THRESHOLD
#     assert pool_session_stats.pairing_range == (settings.PAIRING_THRESHOLD * 71)
def test_create_pool_session_stats_instance(db: Session) -> None:
    """Assert PoolSessionStats instance can be created in the model"""
    category_stats = PoolCategoryStatistics(players=1, threshold=0.85)
    stats = {}
    stats[Categories.BIBLE.value] = category_stats.dict()

    pool_session_stats = pool_session_stats_dao.create(
        db,
        obj_in=PoolSessionStatsCreateSerializer(
            total_players=2, statistics=json.dumps(stats)
        ),
    )

    assert pool_session_stats.total_players == 2
    assert pool_session_stats.statistics is not None
    assert pool_session_stats.statistics[Categories.BIBLE.value]["players"] == 1
    assert (
        pool_session_stats.statistics[Categories.BIBLE.value]["average_score"] is None
    )


def test_create_user_session_stats_instance(
    db: Session,
    create_super_user_instance: Callable,
) -> None:
    """Test UserSessionStats instance can be created in model"""
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    user_session_stats_in = UserSessionStatsCreateSerializer(user_id=user.id)

    user_session_stats = user_session_stats_dao.get_or_create(
        db, obj_in=user_session_stats_in
    )

    assert user_session_stats.total_wins == 0
    assert user_session_stats.total_losses == 0
    assert user_session_stats.sessions_played == 0


def test_update_user_session_stats_instance(
    db: Session,
    create_super_user_instance: Callable,
) -> None:
    """Test UserSessionStats instance can be created in model"""
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    user_session_stats_obj = user_session_stats_dao.get_or_create(
        db, obj_in=UserSessionStatsCreateSerializer(user_id=user.id)
    )
    user_session_stats_in = UserSessionStatsUpdateSerializer(
        sessions_played=1, total_wins=1
    )

    user_session_stats_obj = user_session_stats_dao.update(
        db, db_obj=user_session_stats_obj, obj_in=user_session_stats_in
    )

    assert user_session_stats_obj.total_wins == 1
    assert user_session_stats_obj.total_losses == 0
    assert user_session_stats_obj.sessions_played == 1
    assert user_session_stats_obj.win_ratio == 1.0


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
    mocker: MockerFixture,
    create_session_instance: Callable,
    create_super_user_instance: Callable,
) -> None:
    """Test DuoSession can be created in model"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    session = session_dao.get_not_none(db)
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    data_in = DuoSessionCreateSerializer(
        party_a=user.id,
        status=DuoSessionStatuses.PARTIALLY_REFUNDED.value,
        session_id=session.id,
        amount=settings.SESSION_AMOUNT,
    )
    duo_session = duo_session_dao.create(db, obj_in=data_in)

    assert duo_session.party_a == user.id
    assert duo_session.party_b is None

    assert duo_session.session_id == session.id
    assert duo_session.amount == settings.SESSION_AMOUNT


def test_create_duo_session_instance_fails_if_already_exists(
    db: Session,
    mocker: MockerFixture,
    create_session_instance: Callable,
    create_super_user_instance: Callable,
    delete_duo_session_model_instances: Callable,
) -> None:
    """Test duplicate DuoSessions can not be created in model"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    session = session_dao.get_not_none(db)
    party_a = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)

    party_b = user_dao.get_or_create(
        db, obj_in=UserCreateSerializer(phone="+254764845040")
    )

    # Create DuoSession
    data_in = DuoSessionCreateSerializer(
        party_a=party_a.id,
        party_b=party_b.id,
        winner_id=party_b.id,
        status=DuoSessionStatuses.PAIRED.value,
        session_id=session.id,
        amount=settings.SESSION_AMOUNT,
    )
    duo_session_dao.create(db, obj_in=data_in)

    # Create a similar duo session
    with pytest.raises(DuoSessionFailedOnCreate):
        data_in = DuoSessionCreateSerializer(
            party_a=party_a.id,
            status=DuoSessionStatuses.PARTIALLY_REFUNDED.value,
            session_id=session.id,
            amount=settings.SESSION_AMOUNT,
        )
        duo_session_dao.create(db, obj_in=data_in)

    with pytest.raises(DuoSessionFailedOnCreate):
        data_in = DuoSessionCreateSerializer(
            party_a=party_b.id,
            status=DuoSessionStatuses.PARTIALLY_REFUNDED.value,
            session_id=session.id,
            amount=settings.SESSION_AMOUNT,
        )
        duo_session_dao.create(db, obj_in=data_in)


def test_create_duo_session_instance_fails_if_party_a_and_party_b_are_same(
    db: Session,
    mocker: MockerFixture,
    create_session_instance: Callable,
    create_super_user_instance: Callable,
    delete_duo_session_model_instances: Callable,
) -> None:
    """Test DuoSessions can not be created in model with the same party_a and party_b"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    session = session_dao.get_not_none(db)
    party_a = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)

    with pytest.raises(DuoSessionFailedOnCreate):
        data_in = DuoSessionCreateSerializer(
            party_a=party_a.id,  # party_a is same as party_b
            party_b=party_a.id,  # party_b is same as party_a
            status=DuoSessionStatuses.PARTIALLY_REFUNDED.value,
            session_id=session.id,
            amount=settings.SESSION_AMOUNT,
        )
        duo_session_dao.create(db, obj_in=data_in)


def test_create_duo_session_instance_fails_if_party_b_exists_in_partial_refunds(
    db: Session,
    mocker: MockerFixture,
    create_session_instance: Callable,
    create_super_user_instance: Callable,
    delete_duo_session_model_instances: Callable,
) -> None:
    """Test DuoSessions can not be created in model for partial refunds with party_b"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    session = session_dao.get_not_none(db)
    party_a = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    party_b = user_dao.get_or_create(
        db, obj_in=UserCreateSerializer(phone="+254764845040")
    )

    with pytest.raises(DuoSessionFailedOnCreate):
        data_in = DuoSessionCreateSerializer(
            party_a=party_a.id,
            party_b=party_b.id,
            status=DuoSessionStatuses.PARTIALLY_REFUNDED.value,
            session_id=session.id,
            amount=settings.SESSION_AMOUNT,
        )
        duo_session_dao.create(db, obj_in=data_in)


def test_create_duo_session_instance_fails_if_party_b_exists_in_refunds(
    db: Session,
    mocker: MockerFixture,
    create_session_instance: Callable,
    create_super_user_instance: Callable,
    delete_duo_session_model_instances: Callable,
) -> None:
    """Test DuoSessions can not be created in model for refunds with party_b"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    session = session_dao.get_not_none(db)
    party_a = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    party_b = user_dao.get_or_create(
        db, obj_in=UserCreateSerializer(phone="+254764845040")
    )

    with pytest.raises(DuoSessionFailedOnCreate):
        data_in = DuoSessionCreateSerializer(
            party_a=party_a.id,
            party_b=party_b.id,
            status=DuoSessionStatuses.REFUNDED.value,
            session_id=session.id,
            amount=settings.SESSION_AMOUNT,
        )
        duo_session_dao.create(db, obj_in=data_in)


def test_duo_session_creates_transaction_instance_on_paired_state(
    db: Session,
    mocker: MockerFixture,
    create_session_instance: Callable,
    create_user_model_instances: Callable,
    delete_duo_session_model_instances: Callable,
    delete_transcation_model_instances: Callable,
) -> None:
    """Test that DuoSession creates a transaction after pairing two users"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    session = session_dao.get_not_none(db)
    users = user_dao.get_all(db)

    party_a = users[0]
    party_b = users[1]

    data_in = DuoSessionCreateSerializer(
        party_a=party_a.id,
        party_b=party_b.id,
        winner_id=party_a.id,
        status=DuoSessionStatuses.PAIRED.value,
        session_id=session.id,
        amount=settings.SESSION_AMOUNT,
    )
    duo_session_dao.create(db, obj_in=data_in)

    winner_obj = transaction_dao.get_not_none(db, account=party_a.phone)
    opponent_obj = transaction_dao.get_or_none(db, account=party_b.phone)

    assert float(winner_obj.amount) == (
        settings.SESSION_AMOUNT * settings.SESSION_WIN_RATIO
    )
    assert opponent_obj is None


def test_duo_session_creates_transaction_instance_on_refunded_state(
    db: Session,
    mocker: MockerFixture,
    create_session_instance: Callable,
    create_user_model_instances: Callable,
    delete_duo_session_model_instances: Callable,
    delete_transcation_model_instances: Callable,
) -> None:
    """Test that DuoSession creates a transaction after refunding user"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    session = session_dao.get_not_none(db)
    party_a = user_dao.get_not_none(db)

    data_in = DuoSessionCreateSerializer(
        party_a=party_a.id,
        status=DuoSessionStatuses.REFUNDED.value,
        session_id=session.id,
        amount=settings.SESSION_AMOUNT,
    )
    duo_session_dao.create(db, obj_in=data_in)
    db_obj = transaction_dao.get_not_none(db, account=party_a.phone)

    assert float(db_obj.amount) == (
        settings.SESSION_AMOUNT * settings.SESSION_REFUND_RATIO
    )


def test_duo_session_creates_transaction_instance_on_partially_refunded_state(
    db: Session,
    mocker: MockerFixture,
    create_session_instance: Callable,
    create_user_model_instances: Callable,
    delete_duo_session_model_instances: Callable,
    delete_transcation_model_instances: Callable,
) -> None:
    """Test that DuoSession creates a transaction after partially refunding user"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    session = session_dao.get_not_none(db)
    party_a = user_dao.get_not_none(db)

    data_in = DuoSessionCreateSerializer(
        party_a=party_a.id,
        status=DuoSessionStatuses.PARTIALLY_REFUNDED.value,
        session_id=session.id,
        amount=settings.SESSION_AMOUNT,
    )
    duo_session_dao.create(db, obj_in=data_in)
    db_obj = transaction_dao.get_not_none(db, account=party_a.phone)

    assert float(db_obj.amount) == (
        settings.SESSION_AMOUNT * settings.SESSION_PARTIAL_REFUND_RATIO
    )


# Updates are no longer supported on DuoSession instances
# def test_updated_duo_session_fails_if_user_is_the_same(
#     db: Session,
#     create_session_instance: Callable,
#     create_super_user_instance: Callable,
#     delete_duo_session_model_instances: Callable,
# ):
#     """Test DuoSession fails to pair the same user to themselves"""
#     session = session_dao.get_not_none(db)
#     party_a = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)

#     # Create DuoSession
#     data_in = DuoSessionCreateSerializer(
#         party_a=party_a.id, session_id=session.id, amount=settings.SESSION_AMOUNT
#     )
#     duo_session = duo_session_dao.create(db, obj_in=data_in)

#     with pytest.raises(Exception):
#         # Update the DuoSession
#         duo_session_dao.update(
#             db,
#             db_obj=duo_session,
#             obj_in=DuoSessionUpdateSerializer(
#                 party_b=party_a.id, status=False, winner_id=party_a.id
#             ),
#         )
