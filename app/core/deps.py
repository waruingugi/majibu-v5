from typing import Generator
from sqlalchemy.orm import Session, load_only

from app.db.session import SessionLocal
from app.core.security import (
    OAuth2PasswordBearerWithCookie,
    Auth2PasswordBearerWithCookie,
)
from app.auth.utils.token import check_access_token_is_valid
from app.core.config import settings
from app.core.config import redis
from app.core.helpers import md5_hash
from app.users.models import User
from app.users.daos.user import user_dao

from jose import JWTError, jwt
from fastapi import Depends, Response, Security
from pydantic import ValidationError


def get_db() -> Generator:
    with SessionLocal() as db:
        yield db


oauth2_scheme = OAuth2PasswordBearerWithCookie(
    tokenUrl="/validate-phone/",
)


async def get_decoded_token(
    response: Response,
    db: Session = Depends(get_db),
    token: str = Depends(Auth2PasswordBearerWithCookie()),
) -> dict:
    """Decode the token"""
    import pdb

    pdb.set_trace()

    if check_access_token_is_valid(db, access_token=token):
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": True},
            )

            # ´x-user-id´ response header is used in logging
            response.headers["x-user-id"] = payload["user_id"]
            return payload
        except (JWTError, ValidationError):
            pass
            # raise InvalidToken
    else:
        # First delete the token from redis, then raise an error
        redis.delete(md5_hash(token))
        # raise ExpiredAccessToken


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
        raise
        # raise IncorrectCredentials

    return user


async def get_current_active_user(
    current_user: User = Security(get_current_user),
) -> User:
    if not current_user.is_active:
        raise
        # raise InactiveAccount
    return current_user


async def get_current_active_superuser(
    current_user: User = Security(get_current_user),
) -> User:
    if not user_dao.is_superuser(current_user):
        raise
        # raise InsufficientUserPrivileges
    return current_user
