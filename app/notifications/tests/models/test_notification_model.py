from sqlalchemy.orm import Session

from app.core.config import settings
from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer

from app.notifications.serializers.notifications import CreateNotificationSerializer
from app.notifications.daos.notifications import notifications_dao
from app.notifications.constants import NotificationStatuses, NotificationChannels


def test_create_notification_instance(db: Session) -> None:
    """Test created notification instance has correct default values"""
    phone = settings.SUPERUSER_PHONE
    data_in = CreateNotificationSerializer(
        type="OTP",
        message="0976 is your OTP",
        phone=phone,
        provider="HOST_PINNACLE",
        channel="SMS",
    )
    notification = notifications_dao.create(db, obj_in=data_in)

    assert notification.channel == NotificationChannels.SMS.value
    assert notification.status == NotificationStatuses.CREATED.value
    assert notification.user_id is None


def test_notification_model_relates_to_user_model(db: Session) -> None:
    """Test created notification instance relates to user"""
    phone = settings.SUPERUSER_PHONE
    user_in = UserCreateSerializer(phone=phone)
    user = user_dao.create(db, obj_in=user_in)

    data_in = CreateNotificationSerializer(
        type="OTP",
        message="0976 is your OTP",
        phone=phone,
        provider="HOST_PINNACLE",
        channel="SMS",
        user_id=user.id,
    )

    notification = notifications_dao.create(db, obj_in=data_in)
    assert notification.user_id == user.id
    assert notification.phone == phone
