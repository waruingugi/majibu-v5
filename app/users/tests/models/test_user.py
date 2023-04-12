from sqlalchemy.orm import Session

from app.test_utils.utils import random_phone
from app.users.constants import UserTypes
from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer


def test_create_user(db: Session) -> None:
    """Test created user has correct default values"""
    phone = random_phone()
    user_in = UserCreateSerializer(phone=phone)
    user = user_dao.create(db, obj_in=user_in)

    assert user.phone == phone
    assert user.user_type == UserTypes.PLAYER.value
    assert user.last_login is None
    assert user.date_joined == user.created_at
