from fastapi.testclient import TestClient

from app.quiz.utils import GetSessionQuestions
from app.main import app


def test_get_questions_route_returns_correct_data(
    client: TestClient,
) -> None:
    app.dependency_overrides[GetSessionQuestions] = lambda: lambda result_id: {}

    result_id = "fake_result_id"
    response = client.get("/quiz/questions/" + result_id)

    assert "quiz" in response.context
    assert response.template.name == "quiz/templates/questions.html"
