from pydantic import BaseModel, validator

from app.notifications.constants import (
    NotificationChannels,
    NotificationProviders,
    NotificationTypes,
)


class NotificationBaseSerializer(BaseModel):
    channel: NotificationChannels
    provider: NotificationProviders
    message: str
    recipient: str
    type: str

    @validator("type")
    def validate_notification_type(cls, value):
        notification_types = [
            notification_type.value
            for notification_type in NotificationTypes.__members__.values()
        ]
        if value not in notification_types:
            raise ValueError("Invalid Notification Type")
        return value


class CreateNotificationSerializer(NotificationBaseSerializer):
    ...


class UpdateNotificationSerializer(NotificationBaseSerializer):
    ...
