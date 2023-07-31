from sqlalchemy.orm import Session
from typing import Callable
from datetime import datetime, timedelta
import random

from app.core.config import settings
from app.core.utils import PairUsers
from app.users.daos.user import user_dao
from app.quiz.daos.quiz import result_dao
from app.sessions.daos.session import session_dao
from app.quiz.utils import CalculateScore
from app.quiz.serializers.quiz import ResultCreateSerializer, ResultUpdateSerializer
from pytest_mock import MockerFixture


def test_create_nodes_returns_correct_ordered_score_list(
    db: Session,
    mocker: MockerFixture,
    delete_result_model_instances: Callable,
    create_user_model_instances: Callable,
    create_session_model_instances: Callable,
) -> None:
    """Assert that PairUsers class creates an ordered list of scores"""
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        minutes=settings.SESSION_DURATION
    )

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

    pair_users = PairUsers()
    ordered_score_list = pair_users.ordered_scores_list

    for elem in range(1, len(ordered_score_list)):
        assert ordered_score_list[elem - 1][0] <= ordered_score_list[elem][0]
