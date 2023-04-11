from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import mapped_column
from app.db.base_class import Base
from app.users.constants import UserTypes


class User(Base):
    phone = mapped_column(String, nullable=False, index=True)
    is_active = mapped_column(Boolean, default=True)
    user_type = mapped_column(String, default=UserTypes.PLAYER.value)
    last_login = mapped_column(DateTime, nullable=True)

    @property
    def date_joined(self):
        return self.created_at
