from sqlalchemy.orm import Session, load_only
from app.auth.daos.token import token_dao
from app.auth.models import AuthToken
from datetime import datetime
from app.core.config import redis
from app.core.helpers import md5_hash


def check_access_token_is_valid(db: Session, access_token: str) -> bool:
    if not bool(redis.exists(md5_hash(access_token))):
        """If token does not exist in redis, check if it exists in the db.
        Otherwise return True because it exists in redis."""
        token_obj = token_dao.get_not_none(
            db,
            access_token=access_token,
            load_options=[load_only(AuthToken.access_token_eat, AuthToken.is_active)],
        )

        token_eat = token_obj.access_token_eat if token_obj else None
        return (
            token_eat is not None
            and token_eat >= datetime.utcnow()
            and bool(token_obj.is_active)
        )

    return True
