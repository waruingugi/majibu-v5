from app.db.base_class import Base
from sqlalchemy import String, ForeignKey
from app.notifications.constants import NotificationStatuses
from sqlalchemy.orm import relationship, mapped_column


class Notification(Base):
    status = mapped_column(
        String, default=NotificationStatuses.CREATED.value, nullable=False
    )
    message = mapped_column(String, nullable=False)
    channel = mapped_column(String, nullable=False)
    provider = mapped_column(String, nullable=False)
    recipient_id = mapped_column(
        String, ForeignKey("user.id"), nullable=True, default=None
    )

    user = relationship("User", backref="user")
