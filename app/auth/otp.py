import pyotp
from typing import Dict
import json

from app.auth.serializers.auth import CreateTOTPSerializer
from app.db.base_class import generate_uuid
from app.core.config import redis, settings
from app.core.raw_logger import logger
from app.notifications.serializers.notifications import CreateNotificationSerializer
from app.notifications.constants import NotificationChannels, NotificationTypes
from app.auth.constants import OTP_MESSAGE


class TOTP:
    @staticmethod
    def create(secret: str, length: int = 6, interval: int = 60) -> str:
        """
        Creates a new time otp based on a shared secret
        length - Number of digits on the otp
        interval - lifetime of the otp
        """

        totp = pyotp.TOTP(s=secret, digits=length, interval=interval)
        return totp.now()

    @staticmethod
    def verify(otp: str, secret: str, length: int = 6, interval: int = 60) -> bool:
        """
        Verifies the OTP passed in against the current time OTP.
        """

        totp = pyotp.TOTP(s=secret, digits=length, interval=interval)
        return totp.verify(otp)

    @staticmethod
    def secret() -> str:
        """Generate a random secret."""

        return pyotp.random_base32()


def create_otp(data_in: CreateTOTPSerializer):
    """Create One Time Password for user"""
    logger.info(f"Creating OTP for {data_in.phone}")
    totp_data: Dict[str, str] = {
        "totp_id": generate_uuid(),
        "secret": TOTP.secret(),
    }

    redis.set(data_in.phone, json.dumps(totp_data), ex=settings.TOTP_EXPIRY_TIME)
    totp = TOTP.create(
        totp_data["secret"], settings.TOTP_LENGTH, settings.TOTP_EXPIRY_TIME
    )

    return CreateNotificationSerializer(
        channel=NotificationChannels.SMS.value,
        message=OTP_MESSAGE.format(totp),
        phone=data_in.phone,
        type=NotificationTypes.OTP.value,
    )
