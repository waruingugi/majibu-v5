from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Callable

from app.main import app
from app.errors.custom import ErrorCodes
from app.commons.constants import Categories

from app.accounts.serializers.account import TransactionCreateSerializer
from app.accounts.daos.account import transaction_dao
from app.accounts.tests.test_data import sample_transaction_instance_deposit_1000

from app.core.deps import business_is_open
from app.core.helpers import md5_hash
from app.core.config import redis, settings


def test_post_session_fails_if_business_is_not_open(
    db: Session,
    client: TestClient,
    delete_transcation_model_instances: Callable,
    flush_redis: Callable,
):
    """Test that the request fails if the business is closed"""
    app.dependency_overrides[
        business_is_open
    ] = lambda: False  # Mock business is closed; return False
    obj_in = TransactionCreateSerializer(**sample_transaction_instance_deposit_1000)
    transaction_dao.create(db, obj_in=obj_in)

    response = client.post(
        "/session/summary/", data={"category": Categories.FOOTBALL.value}
    )

    assert response.url.path == "/auth/logout"


def test_post_session_fails_if_there_is_a_recent_withdrawal(
    db: Session,
    client: TestClient,
    flush_redis: Callable,
    delete_transcation_model_instances: Callable,
):
    app.dependency_overrides[
        business_is_open
    ] = lambda: False  # Mock business is closed; return False
    obj_in = TransactionCreateSerializer(**sample_transaction_instance_deposit_1000)
    transaction_dao.create(db, obj_in=obj_in)

    # Set a previous request in redis
    hashed_withdrawal_request = md5_hash(f"{settings.SUPERUSER_PHONE}:withdraw_request")
    redis.set(hashed_withdrawal_request, 100, ex=settings.WITHDRAWAL_BUFFER_PERIOD)

    response = client.post(
        "/session/summary/", data={"category": Categories.FOOTBALL.value}
    )

    assert response.context["server_errors"] == [ErrorCodes.SIMILAR_WITHDRAWAL_REQUEST]
