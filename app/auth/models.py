from app.db.base_class import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship, mapped_column


class AuthToken(Base):
    access_token = mapped_column(String, nullable=False)
    user_id = mapped_column(String, ForeignKey("user.id", ondelete="CASCADE"))
    token_type = mapped_column(String, nullable=False)
    is_active = mapped_column(Boolean, nullable=False, default=True)
    access_token_eat = mapped_column(DateTime, nullable=False)

    user = relationship("User", uselist=False)
