from pydantic import BaseModel

from app.notifications.constants import NotificationChannels, NotificationProviders


class CreateNotificationSerializer(BaseModel):
    channel: NotificationChannels
    provider: NotificationProviders
    message: str | None
    recipient_id: str | None
