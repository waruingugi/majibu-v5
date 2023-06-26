# from sqlalchemy.orm import Session
# from pytest_mock import MockerFixture
# from typing import Callable
# import pytest

# from app.core.config import redis, settings
# from app.core.helpers import md5_hash
# from app.exceptions.custom import WithdrawalRequestInQueue
# from app.sessions.utils import QueryAvailableSession
# from app.users.daos.user import user_dao
# from app.core.helpers import md5_hash
# from app.main import app
# from app.core.deps import get_current_active_user


# def test_query_available_sessions_fails_for_recent_withdrawals(
#     db: Session, mocker: MockerFixture, create_user_instance: Callable
# ) -> None:
#     """Test QueryAvailableSession fails if a previous withdrawal request has been made."""
#     redis.flushall()  # Clear all values from redis

#     # Set a previous request in redis
#     hashed_withdrawal_request = md5_hash(f"{settings.SUPERUSER_PHONE}:withdraw_request")
#     redis.set(hashed_withdrawal_request, 100, ex=settings.WITHDRAWAL_BUFFER_PERIOD)

#     with pytest.raises(WithdrawalRequestInQueue):
#         mocker.patch(
#             "app.sessions.utils.has_sufficient_balance",
#             return_value=True,
#         )
#         user = user_dao.get_not_none(db, phone=settings.SUPERUSER_PHONE)

#         app.dependency_overrides[get_current_active_user] = lambda: user
#         QueryAvailableSession()
