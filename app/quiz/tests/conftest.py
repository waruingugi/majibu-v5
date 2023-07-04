from sqlalchemy.orm import Session
from typing import Callable
import pytest

from app.commons.constants import Categories
from app.commons.utils import generate_uuid
from app.quiz.serializers.quiz import QuestionCreateSerializer, ChoiceCreateSerializer
from app.sessions.serializers.session import SessionCreateSerializer
from app.sessions.daos.session import session_dao
from app.quiz.daos.quiz import question_dao, choice_dao


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
    db: Session, create_question_model_instances: Callable
) -> None:
    """Create 5 Choice model instances based on create_questions_instance"""
    session = session_dao.get_not_none(db)

    for question_id in session.questions:
        choice_in = ChoiceCreateSerializer(
            question_id=question_id, choice_text=generate_uuid()
        )
        choice_dao.create(db, obj_in=choice_in)
