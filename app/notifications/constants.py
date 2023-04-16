from enum import Enum


class NotificationChannels(str, Enum):
    SMS = "SMS"


class NotificationProviders(str, Enum):
    HOST_PINNACLE = "HOST_PINNACLE"


class NotificationTypes(str, Enum):
    OTP = "OTP"


class NotificationStatuses(str, Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"