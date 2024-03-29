from pydantic import BaseModel
from datetime import datetime

from app.core.helpers import _validate_phone_number
from app.users.constants import UserTypes
from app.db.serializer import InDBBaseSerializer


class UserBaseSerializer(BaseModel):
    phone: str
    user_type: str | None = UserTypes.PLAYER.value

    _validate_phone_number = _validate_phone_number


class UserCreateSerializer(UserBaseSerializer):
    ...


class UserUpdateSerializer(UserBaseSerializer):
    is_active: bool | None


class UserInDBSerializer(InDBBaseSerializer, UserBaseSerializer):
    date_joined: datetime
    is_active: bool


class UserReadSerializer(UserBaseSerializer, InDBBaseSerializer):
    pass
