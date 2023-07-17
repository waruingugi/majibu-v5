from fastapi import Request
from fastapi.security.utils import get_authorization_scheme_param
from fastapi import HTTPException
from fastapi import status

from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt

from app.auth.models import AuthToken
from app.core.config import settings, redis
from app.auth.serializers.token import TokenCreateSerializer
from app.auth.constants import TokenGrantType
from app.auth.daos.token import token_dao
from app.core.helpers import md5_hash
from app.core.raw_logger import logger


class Auth2PasswordBearerWithCookie:  # Custom Auth2
    async def __call__(self, request: Request) -> Optional[str]:
        # Changed to accept access token from httpOnly Cookie
        logger.info("Retrieving access token from cookie")
        authorization: str = request.cookies.get("access_token")  # type: ignore

        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return param


class OptionalAuth2PasswordBearerWithCookie:  # Custom Auth2
    async def __call__(self, request: Request) -> Optional[str]:
        # Changed to accept access token from httpOnly Cookie
        logger.info("Running optional search for access token from cookie")
        authorization: str = request.cookies.get("access_token")  # type: ignore

        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            return None
        return param


def clear_redis_tokens(db: Session, user_id: str) -> None:
    """
    Delete user access tokens saved in redis.
    This prevents the user from logging in twice using different devices
    using the token cached in redis.
    token_dao.pre_create accomplishes the same but on the database level
    """
    logger.info(f"Clearing redis tokens related to user id: {user_id}")
    user_tokens = token_dao.get_all(db, user_id=user_id)
    redis_pipeline = redis.pipeline()

    for token in user_tokens:
        redis_pipeline.delete(md5_hash(token.access_token))

    redis_pipeline.execute()


def create_access_token(db: Session, subject: str, grant_type: str) -> dict:
    "Create access token token"
    access_token_ein = settings.ACCESS_TOKEN_EXPIRY_IN_SECONDS

    to_encode = {
        "iat": int(datetime.now().timestamp()),
        "exp": datetime.now() + timedelta(seconds=access_token_ein),
        "user_id": str(subject),
        "grant_type": grant_type,
    }

    # Create access token
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    token_data = {
        "access_token": token,
        "token_type": grant_type,
        "access_token_ein": access_token_ein,
        "user_id": subject,
    }
    return token_data


def get_access_token(db: Session, *, user_id: str) -> AuthToken:
    """Creates access token and saves it to ´AuthToken´ model"""
    token_data = create_access_token(
        db=db, subject=user_id, grant_type=TokenGrantType.CLIENT_CREDENTIALS.value
    )

    obj_in = TokenCreateSerializer(
        user_id=user_id,
        token_type=TokenGrantType.CLIENT_CREDENTIALS,
        access_token=token_data["access_token"],
        access_token_eat=datetime.now()
        + timedelta(seconds=token_data["access_token_ein"]),
        is_active=True,
    )

    # Schedule commands for redis
    # First clear previous tokens from redis
    clear_redis_tokens(db, user_id)

    # (we're stroing access token to avoid querying the db)
    redis_pipeline = redis.pipeline()
    redis_pipeline.set(
        md5_hash(token_data["access_token"]), 1, ex=token_data["access_token_ein"]
    )
    redis_pipeline.execute()

    return token_dao.create(db, obj_in=obj_in)


def insert_token_in_cookie(token_obj: AuthToken) -> str:
    """Set token in cookie header"""
    logger.info("Embedding token in cookie")
    cookie: str = f"access_token=Bearer {token_obj.access_token}; max-age={settings.ACCESS_TOKEN_EXPIRY_IN_SECONDS}; path=/;"  # noqa
    db_connection_url = settings.SQLALCHEMY_DATABASE_URI

    if "@localhost" not in db_connection_url:  # Hack to check if running in prod.
        cookie += " Secure; HttpOnly"

    return cookie
