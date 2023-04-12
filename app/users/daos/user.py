from typing import Optional, Union

from sqlalchemy.orm import Session

from app.db.dao import CRUDDao
from app.users.models import User
from app.users.serializers.user import (
    UserCreateSerializer,
    UserUpdateSerializer,
    UserBaseSerializer,
)
from app.users.constants import UserTypes

# from phonenumbers import parse as parse_phone_number


class UserDao(CRUDDao[User, UserCreateSerializer, UserUpdateSerializer]):
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return self.get(db, phone=username)

    def get_or_create(
        self,
        db: Session,
        obj_in: Union[UserBaseSerializer, UserCreateSerializer],
    ) -> User:
        """Get or create a user"""
        user_in = self.get_by_username(db, username=obj_in.phone)
        if not user_in:
            user_data = UserCreateSerializer(**obj_in.dict())
            user_in = self.create(db, obj_in=user_data)

        return user_in

    # def authenticate_user(self, db: Session, *, username: str, password: str):
    #     user = self.get_by_username(db, username=username)
    #     if not user:
    #         return False
    #     if not verify_password(password, user.hashed_password):
    #         return False
    #     return user

    # def update(
    #     self,
    #     db: Session,
    #     *,
    #     db_obj: User,
    #     obj_in: Union[UserUpdateSerializer, Dict[str, Any]]
    # ) -> User:
    #     if isinstance(obj_in, dict):
    #         update_data = obj_in
    #     else:
    #         update_data = obj_in.dict(exclude_unset=True)

    #     if update_data.get("password", None):
    #         update_data["hashed_password"] = get_password_hash(update_data["password"])

    #     return super().update(db, db_obj=db_obj, obj_in=update_data)

    def is_superuser(self, user: User) -> bool:
        return user.user_type == UserTypes.SUPERADMIN.value


user_dao = UserDao(User)
