from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session
from typing import Callable

from app.quiz.utils import GetSessionQuestions
from app.quiz.daos.quiz import result_dao
from app.main import app


def test_get_questions_route_returns_correct_data(
    client: TestClient,
) -> None:
    """Test the route returns the correct data"""
    app.dependency_overrides[GetSessionQuestions] = lambda: lambda result_id: {}

    result_id = "fake_result_id"
    response = client.get("/quiz/questions/" + result_id)

    assert "quiz" in response.context
    assert response.template.name == "quiz/templates/questions.html"


def test_get_result_score_returns_correct_data(
    db: Session,
    client: TestClient,
    mocker: MockerFixture,
    create_result_instances_to_be_paired: Callable,
) -> None:
    """Test the route returns the correct data"""
    result = result_dao.get_not_none(db)
    mocker.patch("app.quiz.routes.quiz.result_dao.get_not_none", return_value=result)

    response = client.get("/quiz/score/" + result.id)

    assert "score" in response.context
    assert "expires_at" in response.context

    assert "category" in response.context
    assert response.template.name == "quiz/templates/score.html"
