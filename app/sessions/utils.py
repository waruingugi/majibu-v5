from sqlalchemy.orm import Session, load_only
from fastapi import Depends
from typing import Optional
import random

from app.core.deps import (
    has_sufficient_balance,
    get_db,
    get_current_active_user,
)
from app.core.config import redis, settings
from app.core.raw_logger import logger
from app.core.helpers import md5_hash, generate_transaction_code

from app.users.models import User
from app.accounts.daos.account import transaction_dao
from app.accounts.constants import (
    TransactionCashFlow,
    TransactionTypes,
    TransactionStatuses,
    TransactionServices,
    SESSION_WITHDRAWAL_DESCRIPTION,
)
from app.accounts.serializers.account import TransactionCreateSerializer

from app.quiz.daos.quiz import result_dao
from app.quiz.serializers.quiz import ResultCreateSerializer
from app.sessions.filters import DuoSessionFilter, SessionFilter
from app.sessions.constants import DuoSessionStatuses
from app.sessions.daos.session import duo_session_dao, session_dao

from app.quiz.models import Results
from app.exceptions.custom import (
    WithdrawalRequestInQueue,
    InsufficientUserBalance,
    SessionInQueue,
)


class GetAvailableSession:
    def __init__(
        self,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),
    ) -> None:
        """Run validation checks before searching for a session for the user"""
        logger.info(f"Running session validation checks for {user.phone}")
        self.db = db
        self.user = user
        self.category, self.played_session_ids = None, None

        float_is_sufficient = has_sufficient_balance(self.db, user=self.user)
        recent_withdrawals = redis.get(md5_hash(f"{self.user.phone}:withdraw_request"))

        if recent_withdrawals:
            raise WithdrawalRequestInQueue
        if not float_is_sufficient:
            raise InsufficientUserBalance

    def __call__(self, *, category: str, user: Optional[User] = None) -> str | None:
        """Query a session by category that the user can play"""
        self.user = self.user if user is None else user
        self.category = category

        logger.info(f"Query available session for {self.user.phone}")

        active_results = self.query_no_pending_results()

        if not active_results:
            logger.info(f"No active results for {self.user.phone}")
            self.played_session_ids = self.query_sessions_played()
            available_session_ids = self.query_available_pending_duo_sessions()

            if not available_session_ids:
                logger.info(f"No available pending sessions for {self.user.phone}")
                available_session_ids = self.query_available_sessions()

            return (
                random.choice(available_session_ids) if available_session_ids else None
            )

        logger.info(f"A session already exists for {self.user.phone}")
        raise SessionInQueue

    def query_no_pending_results(self) -> bool:
        """Return True if user has a pending session.
        User can only play one session at a time"""
        active_results = result_dao.get_or_none(
            self.db, user_id=self.user.id, is_active=True
        )

        return True if active_results else False

    def query_sessions_played(self) -> list:
        """Query Results and get all session ids played by a user"""
        sessions_played_by_user = result_dao.get_all(
            self.db, user_id=self.user.id, load_options=[load_only(Results.session_id)]
        )
        played_session_ids = list(map(lambda x: x.session_id, sessions_played_by_user))

        return played_session_ids

    def query_available_pending_duo_sessions(self) -> list:
        """
        Query DuoSessions and get all that are pending in the specified category
        but not played by the user.
        """
        available_pending_duo_sessions = duo_session_dao.search(
            self.db,
            search_filter=DuoSessionFilter(
                status=DuoSessionStatuses.PENDING.value,
                session=SessionFilter(
                    category=self.category,
                    id__not_in=self.played_session_ids,
                ),  # type: ignore
            ),
        )

        available_session_ids = list(
            map(lambda x: x.session_id, available_pending_duo_sessions)
        )

        # Remove duplicates and return list
        return list(dict.fromkeys(available_session_ids))

    def query_available_sessions(self) -> list:
        """Query Sessions model by category for an id the user has not played."""
        available_sessions = session_dao.search(
            self.db,
            search_filter=SessionFilter(
                id__not_in=self.played_session_ids, category=self.category
            ),  # type: ignore
        )

        available_session_ids = list(map(lambda x: x.id, available_sessions))
        return available_session_ids


def create_session(db: Session, *, user: User, session_id: str) -> str | None:
    """Create a result instance for the user
    This includes deducting user balance for a user"""
    if has_sufficient_balance(db, user=user):  # A redudancy check
        description = SESSION_WITHDRAWAL_DESCRIPTION.format(user.phone, session_id)

        # Withdraw the session amount from the user's wallet
        logger.info(
            "Create withdrawal request for user {user.phone} for session id: {session_id}"
        )
        transaction_dao.create(
            db,
            obj_in=TransactionCreateSerializer(
                account=user.phone,
                external_transaction_id=generate_transaction_code(),
                cash_flow=TransactionCashFlow.OUTWARD.value,
                type=TransactionTypes.WITHDRAWAL.value,
                status=TransactionStatuses.SUCCESSFUL.value,
                service=TransactionServices.MAJIBU.value,
                description=description,
                amount=settings.SESSION_AMOUNT,
                fee=0.0,  # No fee for session withdrawals
                tax=0.0,  # No tax for session withdrawals
            ),
        )

        # Create the result instance
        # This is what will be updated when they post their answers
        result_in = ResultCreateSerializer(user_id=user.id, session_id=session_id)
        result_obj = result_dao.create(db, obj_in=result_in)

        return result_obj.id

    # If user balance is not sufficient, raise error: a redudancy check
    raise InsufficientUserBalance
