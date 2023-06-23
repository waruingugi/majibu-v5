from sqlalchemy.orm import Session
from fastapi import Depends

from app.users.models import User
from app.core.helpers import md5_hash
from app.core.deps import (
    has_sufficient_balance,
    get_db,
    get_current_active_user,
)
from app.core.config import redis
from app.exceptions.custom import WithdrawalRequestInQueue, InsufficientUserBalance


async def assert_no_recent_withdrawals(db: Session, user: User):
    """Check no withdrawal transactions are in queue"""
    float_is_sufficient = has_sufficient_balance(db, user=user)
    recent_withdrawals = redis.get(md5_hash(f"{user.phone}:withdraw_request"))

    if recent_withdrawals:
        raise WithdrawalRequestInQueue
    if not float_is_sufficient:
        raise InsufficientUserBalance


class QueryAvailableSession:
    def __init__(
        self,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),
    ) -> None:
        self.db = db
        self.user = user

        float_is_sufficient = has_sufficient_balance(self.db, user=self.user)
        recent_withdrawals = redis.get(md5_hash(f"{self.user.phone}:withdraw_request"))

        if recent_withdrawals:
            raise WithdrawalRequestInQueue
        if not float_is_sufficient:
            raise InsufficientUserBalance

    def __call__(self, *, category: str) -> None:
        pass


# receive category name: call other function
# Query sessions in duo session which are pending and category
# Query user sessions in result and category
# sessions - result = get session
# If not choose random session and not in query
