from app.auth.serializers.auth import CreateOTPSerializer
from app.auth.otp import create_otp
from app.core.config import settings, redis
from app.notifications.constants import NotificationChannels, NotificationTypes


def test_create_otp():
    phone = settings.SUPERUSER_PHONE
    data = CreateOTPSerializer(phone=phone)
    response = create_otp(data)
    cached_data = redis.get(phone)

    assert cached_data is not None
    assert response.channel == NotificationChannels.SMS.value
    assert response.phone == phone
    assert response.type == NotificationTypes.OTP.value
