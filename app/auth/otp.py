import pyotp
from typing import Dict
import json

from app.auth.serializers.auth import CreateOTPSerializer
from app.db.base_class import generate_uuid
from app.core.config import redis, settings
from app.core.raw_logger import logger
from app.notifications.serializers.notifications import CreateNotificationSerializer
from app.notifications.constants import NotificationChannels, NotificationTypes
from app.auth.serializers.auth import ValidateOTPSerializer
from app.auth.constants import OTP_MESSAGE
from app.core.helpers import md5_hash


class TOTP:
    @staticmethod
    def create(
        secret: str,
        length: int = settings.TOTP_LENGTH,
        interval: int = settings.TOTP_EXPIRY_TIME,
    ) -> str:
        """
        Creates a new time otp based on a shared secret
        length - Number of digits on the otp
        interval - lifetime of the otp
        """

        totp = pyotp.TOTP(s=secret, digits=length, interval=interval)
        return totp.now()

    @staticmethod
    def verify(
        otp: str,
        secret: str,
        length: int = settings.TOTP_LENGTH,
        interval: int = settings.TOTP_EXPIRY_TIME,
    ) -> bool:
        """
        Verifies the OTP passed in against the current time OTP.
        """

        totp = pyotp.TOTP(s=secret, digits=length, interval=interval)
        return totp.verify(otp)

    @staticmethod
    def secret() -> str:
        """Generate a random secret."""

        return pyotp.random_base32()


def create_otp(data_in: CreateOTPSerializer):
    """Create One Time Password for user"""
    logger.info(f"Creating OTP for {data_in.phone}")
    totp_data: Dict[str, str] = {
        "totp_id": generate_uuid(),
        "secret": TOTP.secret(),
    }

    redis.set(
        md5_hash(data_in.phone), json.dumps(totp_data), ex=settings.TOTP_EXPIRY_TIME
    )
    totp = TOTP.create(
        totp_data["secret"], settings.TOTP_LENGTH, settings.TOTP_EXPIRY_TIME
    )

    return CreateNotificationSerializer(
        channel=NotificationChannels.SMS.value,
        message=OTP_MESSAGE.format(totp),
        phone=data_in.phone,
        type=NotificationTypes.OTP.value,
    )


def validate_otp(data_in: ValidateOTPSerializer):
    """Validate OTP submitted by user"""
    logger.info(f"Validating OTP for {data_in.phone}")
    user_otp_data = redis.get(md5_hash(data_in.phone))

    if user_otp_data is not None:
        totp_data = json.loads(user_otp_data)

        return TOTP.verify(
            otp=data_in.otp,
            secret=totp_data["secret"],
        )

    logger.info(f"Invalid OTP shared by {data_in.phone}")
    return False
