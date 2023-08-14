from fastapi.testclient import TestClient

from app.db.session import SessionLocal, get_engine
from app.db.base import Base
from app.main import app

from app.commons.constants import Categories
from app.commons.utils import generate_uuid, random_phone
from app.quiz.serializers.quiz import ResultCreateSerializer, ResultUpdateSerializer
from app.quiz.daos.quiz import result_dao
from app.quiz.utils import CalculateScore

from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer
from app.sessions.daos.session import session_dao, pool_session_stats_dao
from app.sessions.serializers.session import SessionCreateSerializer

from app.core.config import settings, redis
from app.core.deps import get_current_active_user
from app.accounts.daos.mpesa import mpesa_payment_dao, withdrawal_dao
from app.accounts.daos.account import transaction_dao

from sqlalchemy.orm import Session
from typing import Generator, Callable
import random
import pytest


@pytest.fixture
def flush_redis() -> None:
    redis.flushall()


@pytest.fixture
def create_super_user_instance(db: Session) -> None:
    """Create a user"""
    user_dao.get_or_create(
        db, obj_in=UserCreateSerializer(phone=settings.SUPERUSER_PHONE)
    )


@pytest.fixture
def create_user_model_instances(db: Session) -> None:
    """Create several user model instances"""
    for i in range(10):
        user_dao.get_or_create(db, obj_in=UserCreateSerializer(phone=random_phone()))


@pytest.fixture
def create_session_instance(db: Session) -> None:
    """Create a session instance"""
    question_ids = [generate_uuid() for i in range(settings.QUESTIONS_IN_SESSION)]

    session_dao.create(
        db,
        obj_in=SessionCreateSerializer(
            category=Categories.BIBLE.value, questions=question_ids
        ),
    )


@pytest.fixture
def delete_session_model_instances(db: Session) -> None:
    """Delete all existing rows in Sessions model"""
    sessions = session_dao.get_all(db)
    for session in sessions:
        session_dao.remove(db, id=session.id)


@pytest.fixture
def delete_result_model_instances(db: Session) -> None:
    """Delete all existing rows in Results model"""
    results = result_dao.get_all(db)
    for result in results:
        result_dao.remove(db, id=result.id)


@pytest.fixture
def delete_pool_session_stats_model_instances(db: Session) -> None:
    """Delete all existing rows in PoolSessionStats model"""
    pool_session_stats = pool_session_stats_dao.get_all(db)
    for stat in pool_session_stats:
        pool_session_stats_dao.remove(db, id=stat.id)


@pytest.fixture
def delete_withdrawal_model_instances(db: Session) -> None:
    """Delete previously existing rows in Transactions model"""
    previous_withdrawals = withdrawal_dao.get_all(db)
    for transaction in previous_withdrawals:
        withdrawal_dao.remove(db, id=transaction.id)


@pytest.fixture
def delete_transcation_model_instances(db: Session) -> None:
    # Delete previously existing rows in Transactions model
    previous_transactions = transaction_dao.get_all(db)
    for transaction in previous_transactions:
        transaction_dao.remove(db, id=transaction.id)


@pytest.fixture
def delete_previous_mpesa_payment_transactions(db: Session) -> None:
    # Delete previously existing rows in Mpesa Payments model
    previous_transactions = mpesa_payment_dao.get_all(db)
    for transaction in previous_transactions:
        mpesa_payment_dao.remove(db, id=transaction.id)


@pytest.fixture
def create_session_model_instances(
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
def create_result_instances_to_be_paired(
    db: Session,
    delete_result_model_instances: Callable,
    create_user_model_instances: Callable,
    create_session_model_instances: Callable,
) -> None:
    """Create a random set of results that can be used to create a duo session"""
    users = user_dao.get_all(db)
    sessions = session_dao.get_all(db)

    for user in users:
        session = random.choice(sessions)
        result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
        result_obj = result_dao.create(db, obj_in=result_in)

        calculate_score = CalculateScore(db, user)
        final_score = calculate_score.calculate_final_score(
            random.uniform(0, settings.SESSION_TOTAL_ANSWERED_WEIGHT),
            random.uniform(0, settings.SESSION_CORRECT_ANSWERED_WEIGHT),
        )
        total_correct = random.randint(0, settings.QUESTIONS_IN_SESSION)
        total_answered = random.randint(0, total_correct)
        moderated_score = calculate_score.moderate_score(final_score)

        result_in = ResultUpdateSerializer(
            total_correct=total_correct,
            total_answered=total_answered,
            total=final_score,
            score=moderated_score,
        )
        result_dao.update(db, db_obj=result_obj, obj_in=result_in)


@pytest.fixture(scope="session")
def db() -> Generator:
    # Create the db to be used in tests
    Base.metadata.create_all(bind=get_engine())
    with SessionLocal() as db:
        yield db

    Base.metadata.drop_all(bind=get_engine())


def mock_create_user():
    with SessionLocal() as db:
        user = user_dao.get_or_create(
            db, obj_in=UserCreateSerializer(phone=settings.SUPERUSER_PHONE)
        )
        return user


@pytest.fixture(scope="session")
def client():
    Base.metadata.create_all(bind=get_engine())

    with TestClient(app) as client:
        # using dependency overrides to mock the function get_current_active_user
        app.dependency_overrides[get_current_active_user] = mock_create_user

        yield client
