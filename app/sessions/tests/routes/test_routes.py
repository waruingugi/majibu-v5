from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from typing import Callable

from app.main import app
from app.errors.custom import ErrorCodes
from app.commons.constants import Categories
from app.sessions.utils import GetAvailableSession
from app.quiz.utils import GetSessionQuestions

from app.accounts.daos.account import transaction_dao
from app.accounts.serializers.account import TransactionCreateSerializer
from app.accounts.tests.test_data import sample_transaction_instance_deposit_1000

from app.core.deps import business_is_open
from app.core.helpers import md5_hash
from app.core.config import redis, settings


def test_post_session_fails_if_business_is_not_open(
    db: Session,
    client: TestClient,
    delete_transcation_model_instances: Callable,
    flush_redis: Callable,
) -> None:
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
) -> None:
    """Test that the request fails if user made a withdrawal recently"""
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


def test_post_session_raises_no_available_session_exception(
    db: Session,
    client: TestClient,
) -> None:
    """Test that the request redirects if no session was found for the user"""
    app.dependency_overrides[
        business_is_open
    ] = lambda: True  # Mock business is open; return True
    app.dependency_overrides[
        GetAvailableSession
    ] = lambda: lambda category, user: None  # Fancy one liner to mock class
    response = client.post(
        "/session/summary/", data={"category": Categories.FOOTBALL.value}
    )

    assert response.context["server_errors"] == [ErrorCodes.NO_AVAILABLE_SESSION]


def test_post_session_redirects_to_get_question_route(
    db: Session,
    mocker: MockerFixture,
    client: TestClient,
) -> None:
    """Test that the route successfully redirects when a sessions is found for the user"""
    app.dependency_overrides[
        business_is_open
    ] = lambda: True  # Mock business is open; return True
    app.dependency_overrides[
        GetAvailableSession
    ] = (
        lambda: lambda category, user: "fake_session_id"
    )  # Fancy one liner to mock class
    app.dependency_overrides[GetSessionQuestions] = lambda: lambda result_id: {}
    mocker.patch(
        "app.sessions.routes.session.create_session",
        return_value="fake_result_id",
    )
    response = client.post(
        "/session/summary/", data={"category": Categories.FOOTBALL.value}
    )

    assert response.template.name == "quiz/templates/questions.html"


def test_get_sessions_history_returns_correct_data(
    db: Session,
    client: TestClient,
    mocker: MockerFixture,
) -> None:
    """Test the route returns the correct data"""
    mocker.patch("app.sessions.routes.session.view_session_history", return_value=[])

    response = client.get("/session/history")

    assert "sessions_history" in response.context
    assert response.template.name == "sessions/templates/history.html"


def test_get_landing_page_shows_correctly(
    db: Session,
    client: TestClient,
) -> None:
    """Test that the landing page shows correctly"""
    response = client.get("/session/")
    assert response.template.name == "sessions/templates/landing.html"
