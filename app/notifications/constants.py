from enum import Enum


class NotificationChannels(str, Enum):
    SMS = "SMS"


class NotificationProviders(str, Enum):
    HOST_PINNACLE = "HOST_PINNACLE"
