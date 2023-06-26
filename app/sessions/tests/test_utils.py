# from sqlalchemy.orm import Session
# from pytest_mock import MockerFixture
# from typing import Callable

# from app.core.config import settings
# from app.sessions.utils import QueryAvailableSession
# from app.users.daos.user import user_dao


# def test_query_available_sessions_fails_for_recent_withdrawals(
#     db: Session, mocker: MockerFixture, create_user_instance: Callable
# ) -> None:
#     mocker.patch(
#         "app.sessions.utils.has_sufficient_balance",
#         return_value=True,
#     )
#     # user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)

#     # query_available_session = QueryAvailableSession(db, user)
#     # query_available_session(category='BIBLE')
