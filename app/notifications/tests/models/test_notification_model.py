from sqlalchemy.orm import Session

from app.notifications.serializers.notifications import CreateNotificationSerializer
from app.notifications.daos.notifications import notifications_dao
from app.notifications.constants import NotificationStatuses, NotificationChannels
from app.core.config import settings


def test_create_notification_instance(db: Session) -> None:
    """Test created notification instance has correct default values"""
    data_in = CreateNotificationSerializer(
        type="OTP",
        message="0976 is your OTP",
        recipient=settings.SUPERUSER_PHONE[1:],
        provider="HOST_PINNACLE",
        channel="SMS",
    )
    notification = notifications_dao.create(db, obj_in=data_in)

    assert notification.channel == NotificationChannels.SMS.value
    assert notification.status == NotificationStatuses.CREATED.value
    assert notification.user_id is None
