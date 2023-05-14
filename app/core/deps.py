from typing import Generator, Dict
from sqlalchemy.orm import Session, load_only

from app.db.session import SessionLocal
from app.core.security import (
    Auth2PasswordBearerWithCookie,
    OptionalAuth2PasswordBearerWithCookie,
)
from app.auth.utils.token import check_access_token_is_valid
from app.core.config import settings, redis
from app.core.raw_logger import logger
from app.core.helpers import md5_hash
from app.users.models import User
from app.users.daos.user import user_dao
from app.exceptions.custom import (
    InvalidToken,
    ExpiredAccessToken,
    IncorrectCredentials,
    InactiveAccount,
    InsufficientUserPrivileges,
)
from app.accounts.daos.account import transaction_dao

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
    if current_user:
        if current_user.is_active:
            return current_user

    return None


async def get_current_active_user(
    current_user: User = Security(get_current_user),
) -> User:
    if not current_user.is_active:
        raise InactiveAccount
    return current_user


async def get_current_active_superuser(
    current_user: User = Security(get_current_user),
) -> User:
    if not user_dao.is_superuser(current_user):
        raise InsufficientUserPrivileges
    return current_user


async def get_user_balance(
    user: User = Security(get_current_user),
    db: Session = Depends(get_db),
) -> float:
    logger.info(f"Get user: {user.phone} balance")

    latest_transaction = transaction_dao.get_or_none(
        db, {"order_by": ["-created_at"], "account": user.phone}
    )
    current_balance = 0.00
    if latest_transaction:
        current_balance = latest_transaction.final_balance

    return current_balance
