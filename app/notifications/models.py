from app.db.base_class import Base
from app.notifications.constants import NotificationStatuses
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import relationship, mapped_column


class Notification(Base):
    status = mapped_column(
        String, default=NotificationStatuses.CREATED.value, nullable=False
    )
    type = mapped_column(String, nullable=False)
    message = mapped_column(String, nullable=False)
    channel = mapped_column(String, nullable=False)
    provider = mapped_column(String, nullable=False)
    phone = mapped_column(String, nullable=False)
    user_id = mapped_column(String, ForeignKey("user.id"), nullable=True, default=None)

    user = relationship("User", backref="notification")
