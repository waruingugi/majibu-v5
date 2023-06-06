from sqlalchemy.orm import Session

from app.commons.constants import Categories
from app.quiz.daos.quiz import question_dao
from app.quiz.serializers.quiz import QuestionCreateSerializer


def test_create_question(db: Session) -> None:
    """Test question can be created successfully"""
    question_text = "Random question"
    user_in = QuestionCreateSerializer(
        question_text=question_text, category=Categories.FOOTBALL.value
    )
    question = question_dao.create(db, obj_in=user_in)

    assert question.question_text == question_text
    assert question.category == Categories.FOOTBALL.value
