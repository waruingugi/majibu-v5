from sqlalchemy.orm import Session
from typing import Callable

from app.commons.constants import Categories
from app.core.config import settings

from app.sessions.daos.session import session_dao
from app.users.daos.user import user_dao
from app.quiz.daos.quiz import question_dao, choice_dao, answer_dao, result_dao
from app.quiz.serializers.quiz import (
    QuestionCreateSerializer,
    ChoiceCreateSerializer,
    AnswerCreateSerializer,
    ResultCreateSerializer,
)


def test_create_question_instance(db: Session) -> None:
    """Test question can be created successfully"""
    question_text = "Random question"
    question_in = QuestionCreateSerializer(
        question_text=question_text, category=Categories.FOOTBALL.value
    )
    question = question_dao.create(db, obj_in=question_in)

    assert question.question_text == question_text
    assert question.category == Categories.FOOTBALL.value


def test_update_question_instance(db: Session) -> None:
    """Test question can be updated successfully"""
    invalid_question = "Invalid question"
    question = question_dao.create(
        db,
        obj_in=QuestionCreateSerializer(
            question_text=invalid_question, category=Categories.FOOTBALL.value
        ),
    )

    updated_question = question_dao.update(
        db, db_obj=question, obj_in={"question_text": "Valid question"}
    )

    assert updated_question.question_text == "Valid question"
    assert updated_question.category == Categories.FOOTBALL.value


def test_create_choice_instance(db: Session) -> None:
    """Test create question"""
    question_in = QuestionCreateSerializer(
        question_text="Random question", category=Categories.FOOTBALL.value
    )
    question = question_dao.create(db, obj_in=question_in)

    choice_text = "Choice text"
    choice = choice_dao.create(
        db,
        obj_in=ChoiceCreateSerializer(question_id=question.id, choice_text=choice_text),
    )

    assert choice.choice_text == choice_text
    assert choice.question_id == question.id


def test_create_answer_instance(db: Session) -> None:
    """Test create answer instance"""
    question_in = QuestionCreateSerializer(
        question_text="Random question", category=Categories.FOOTBALL.value
    )
    question = question_dao.create(db, obj_in=question_in)

    choice = choice_dao.create(
        db,
        obj_in=ChoiceCreateSerializer(
            question_id=question.id, choice_text="Random choice"
        ),
    )

    answer = answer_dao.create(
        db, obj_in=AnswerCreateSerializer(question_id=question.id, choice_id=choice.id)
    )

    assert answer.choice_id == choice.id
    assert answer.question_id == question.id


def test_create_results_instance(
    db: Session, create_user_instance: Callable, create_session_instance: Callable
) -> None:
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    session = session_dao.get_not_none(db, category=Categories.BIBLE.value)

    result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
    result = result_dao.create(db, obj_in=result_in)

    assert result.user_id == user.id
    assert result.session_id == session.id

    assert result.speed == 0.0
    assert result.total_answered == 0.0

    assert result.percentage == 0.0
    assert result.score == 0.0

    assert result.is_active is True
    time_diff = (result.expires_at - result.created_at).total_seconds()
    assert round(time_diff) == settings.SESSION_DURATION
