from pydantic import BaseModel, validator

from app.notifications.constants import (
    NotificationChannels,
    NotificationProviders,
    NotificationTypes,
)


# Validators
# ----------------------------------------------------------------------------
def validate_notification_type(type: str):
    notification_types = [
        notification_type.value
        for notification_type in NotificationTypes.__members__.values()
    ]
    if type not in notification_types:
        raise ValueError("Invalid Notification Type")
    return type


_validate_notification_type = validator("type", pre=True, allow_reuse=True)(
    validate_notification_type
)


def validate_notification_channel(channel: str):
    notification_channels = [
        notification_channel.value
        for notification_channel in NotificationChannels.__members__.values()
    ]
    if channel not in notification_channels:
        raise ValueError("Invalid Notification Channel")
    return channel


_validate_notification_channel = validator("channel", pre=True, allow_reuse=True)(
    validate_notification_channel
)


def validate_notification_provider(provider: str):
    notification_providers = [
        notification_provider.value
        for notification_provider in NotificationProviders.__members__.values()
    ]
    if provider not in notification_providers:
        raise ValueError("Invalid Notification Provider")
    return provider


_validate_notification_provider = validator("provider", pre=True, allow_reuse=True)(
    validate_notification_provider
)
# ----------------------------------------------------------------------------


class NotificationBaseSerializer(BaseModel):
    channel: str
    provider: str
    message: str
    recipient: str
    type: str

    _validate_notification_type = _validate_notification_type
    _validate_notification_channel = _validate_notification_channel
    _validate_notification_provider = _validate_notification_provider


class CreateNotificationSerializer(NotificationBaseSerializer):
    ...


class UpdateNotificationSerializer(NotificationBaseSerializer):
    ...
