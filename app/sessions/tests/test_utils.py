from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from typing import Callable
import pytest

from app.core.config import settings
from app.commons.constants import Categories
from app.sessions.utils import QueryAvailableSession
from app.sessions.daos.session import session_dao
from app.users.daos.user import user_dao
from app.quiz.daos.quiz import result_dao
from app.quiz.serializers.quiz import ResultCreateSerializer
from app.exceptions.custom import SessionInQueue


def test_query_available_sessions_fails_if_active_results(
    db: Session,
    mocker: MockerFixture,
    create_user_instance: Callable,
    create_session_instance: Callable,
) -> None:
    """Test the class fails if there is  an active session/active result"""
    mocker.patch(
        "app.sessions.utils.has_sufficient_balance",
        return_value=True,
    )
    user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)
    session = session_dao.get_not_none(db, category=Categories.BIBLE.value)

    result_in = ResultCreateSerializer(user_id=user.id, session_id=session.id)
    result_dao.create(db, obj_in=result_in)

    with pytest.raises(SessionInQueue):
        query_available_session = QueryAvailableSession(db, user)
        _ = query_available_session(category=Categories.FOOTBALL.value)
