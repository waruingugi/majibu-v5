import pytest
import random
from typing import Callable
from sqlalchemy.orm import Session

from app.users.daos.user import user_dao
from app.quiz.daos.quiz import result_dao
from app.sessions.daos.session import session_dao
from app.quiz.serializers.quiz import (
    ResultCreateSerializer,
    ResultUpdateSerializer,
)
from app.quiz.utils import CalculateScore
from app.core.config import settings


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
