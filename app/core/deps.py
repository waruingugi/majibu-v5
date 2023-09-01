from typing import Generator, Dict, Callable
from sqlalchemy.orm import Session, load_only
from datetime import datetime

from app.db.session import SessionLocal
from app.core.security import (
    Auth2PasswordBearerWithCookie,
    OptionalAuth2PasswordBearerWithCookie,
)
from app.auth.utils.token import check_access_token_is_valid
from app.accounts.daos.account import transaction_dao
from app.core.config import settings, redis
from app.core.helpers import md5_hash
from app.users.models import User
from app.users.daos.user import user_dao
from app.exceptions.custom import (
    InvalidToken,
    ExpiredAccessToken,
    IncorrectCredentials,
    InactiveAccount,
    InsufficientUserPrivileges,
    BusinessInMaintenanceMode,
)

from jose import JWTError, jwt
from fastapi import Depends, Security, Request
from pydantic import ValidationError
from starlette.datastructures import MutableHeaders


def get_db() -> Generator:
    with SessionLocal() as db:
        yield db


async def get_decoded_token(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(Auth2PasswordBearerWithCookie()),
) -> Dict | None:
    """Decode the token"""
    if check_access_token_is_valid(db, access_token=token):
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": True},
            )

            # ´x-user-id´ response header is used in logging
            """In APIs, we set this in the response header. However, because we're
            """
            request_header = MutableHeaders(request._headers)
            request_header["x-user-id"] = payload["user_id"]
            request._headers = request_header

            return payload
        except (JWTError, ValidationError):
            raise InvalidToken
    else:
        # First delete the token from redis, then raise an error
        redis.delete(md5_hash(token))
        raise ExpiredAccessToken


async def get_decoded_token_or_none(
    db: Session = Depends(get_db),
    token: str = Depends(OptionalAuth2PasswordBearerWithCookie()),
) -> Dict | None:
    """Decode the token if it exists else return None"""
    if token:
        if check_access_token_is_valid(db, access_token=token):
            try:
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                    options={"verify_exp": True},
                )

                return payload
            except (JWTError, ValidationError):
                return None

    return None


async def get_current_user_or_none(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(get_decoded_token_or_none),
) -> User | None:
    """Get current user or return None"""
    if token_payload is not None:
        user = user_dao.get(
            db,
            id=token_payload["user_id"],
            load_options=[load_only(User.id)],
        )

        return user

    return None


async def get_current_user(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(get_decoded_token),
) -> User:
    """Get current user"""
    user = user_dao.get(
        db,
        id=token_payload["user_id"],
        load_options=[load_only(User.id)],
    )
    if user is None:
        raise IncorrectCredentials

    return user


async def get_current_active_user_or_none(
    current_user: User = Security(get_current_user_or_none),
) -> User | None:
    """Get current active user or return None"""
    if current_user:
        if current_user.is_active:
            return current_user

    return None


async def get_current_active_user(
    current_user: User = Security(get_current_user),
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise InactiveAccount
    return current_user


async def get_current_active_superuser(
    current_user: User = Security(get_current_user),
) -> User:
    """Get current active user"""
    if not user_dao.is_superuser(current_user):
        raise InsufficientUserPrivileges
    return current_user


async def business_in_maintenance_mode() -> None:
    """Raise error if business is in maintenance mode."""
    if settings.MAINTENANCE_MODE:
        raise BusinessInMaintenanceMode


async def business_is_open(
    _: Callable = Depends(business_in_maintenance_mode),
) -> bool:
    """Check business is open or business is within operating hours"""
    # Calculate the current time in EAT
    eat_now = datetime.now()

    # Extract the time components from open_time and close_time
    open_hour, open_minute = map(int, settings.BUSINESS_OPENS_AT.split(":"))
    close_hour, close_minute = map(int, settings.BUSINESS_CLOSES_AT.split(":"))

    # Create datetime objects for the current time, open time, and close time
    current_datetime = datetime(
        year=eat_now.year,
        month=eat_now.month,
        day=eat_now.day,
        hour=eat_now.hour,
        minute=eat_now.minute,
    )
    business_opens_at = datetime(
        year=eat_now.year,
        month=eat_now.month,
        day=eat_now.day,
        hour=open_hour,
        minute=open_minute,
    )
    business_closes_at = datetime(
        year=eat_now.year,
        month=eat_now.month,
        day=eat_now.day,
        hour=close_hour,
        minute=close_minute,
    )

    # Check if the current time is within the specified range
    if business_opens_at <= current_datetime <= business_closes_at:
        return True
    else:
        return False


def has_sufficient_balance(
    db: Session, *, user: User, amount: float = settings.SESSION_AMOUNT
) -> bool:
    """Assert that the user has sufficient balance to meet required amount"""
    wallet_balance = transaction_dao.get_user_balance(db, account=user.phone)
    balance_is_sufficient = wallet_balance >= amount
    return balance_is_sufficient
