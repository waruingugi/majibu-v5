from fastapi_sqlalchemy_filter import Filter
from app.users.models import User


class UserBaseFilter(Filter):
    phone: str | None

    class Constants(Filter.Constants):
        model = User


class UserFilter(UserBaseFilter):
    is_active: bool | None
    user_type: str | None
