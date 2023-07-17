from sqlalchemy.orm import Session
from typing import Callable
import pytest

from app.commons.constants import Categories
from app.commons.utils import generate_uuid
from app.quiz.serializers.quiz import (
    QuestionCreateSerializer,
    ChoiceCreateSerializer,
    AnswerCreateSerializer,
)
from app.quiz.daos.quiz import question_dao, choice_dao, user_answer_dao, answer_dao
from app.sessions.serializers.session import SessionCreateSerializer
from app.sessions.daos.session import session_dao
from app.core.config import settings


@pytest.fixture
def delete_user_answer_model_instances(db: Session) -> None:
    """Delete all existing rows in UserAnswer model"""
    user_answers = user_answer_dao.get_all(db)
    for answer in user_answers:
        user_answer_dao.remove(db, id=answer.id)


@pytest.fixture
def delete_answer_model_instances(db: Session) -> None:
    """Delete all existing rows in Answer model"""
    answers = answer_dao.get_all(db)
    for answer in answers:
        answer_dao.remove(db, id=answer.id)


@pytest.fixture
def delete_choice_model_instances(db: Session) -> None:
    """Delete all existing rows in Choice model"""
    choices = choice_dao.get_all(db)
    for choice in choices:
        choice_dao.remove(db, id=choice.id)


@pytest.fixture
def create_question_model_instances(
    db: Session, delete_session_model_instances: Callable
) -> None:
    """Create 5 Question model instances"""
    question_ids = []
    for i in range(5):
        question_in = QuestionCreateSerializer(
            category=Categories.BIBLE.value, question_text=generate_uuid()
        )
        question = question_dao.create(db, obj_in=question_in)
        question_ids.append(question.id)

    session_dao.create(
        db,
        obj_in=SessionCreateSerializer(
            category=Categories.BIBLE.value, questions=question_ids
        ),
    )


@pytest.fixture
def create_choice_model_instances(
    db: Session,
    delete_answer_model_instances: Callable,
    delete_choice_model_instances: Callable,
    create_question_model_instances: Callable,
) -> None:
    """Create 5 Choice model instances based on create_questions_instance"""
    session = session_dao.get_not_none(db)

    for question_id in session.questions:
        for i in range(settings.CHOICES_IN_QUESTION):
            choice_in = ChoiceCreateSerializer(
                question_id=question_id, choice_text=generate_uuid()
            )
            choice = choice_dao.create(db, obj_in=choice_in)

            answer_dao.get_or_create(
                db,
                obj_in=AnswerCreateSerializer(
                    question_id=question_id, choice_id=choice.id
                ),
            )
