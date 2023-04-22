from app.auth.serializers.auth import CreateOTPSerializer, ValidateOTPSerializer
from app.auth.otp import create_otp, validate_otp
from app.core.config import settings, redis
from app.core.helpers import md5_hash
from app.notifications.constants import NotificationChannels, NotificationTypes

import unittest
import re


class TestOTP(unittest.TestCase):
    phone = settings.SUPERUSER_PHONE
    data = CreateOTPSerializer(phone=phone)

    def test_create_otp(self):
        """Test successful creation of OTP"""
        response = create_otp(self.data)
        cached_data = redis.get(md5_hash(self.phone))

        self.assertIsNotNone(cached_data)
        self.assertEqual(response.channel, NotificationChannels.SMS.value)
        self.assertEqual(response.phone, self.phone)
        self.assertEqual(response.type, NotificationTypes.OTP.value)

    def test_validate_otp(self):
        """Test valid OTP is accepted"""
        response = create_otp(self.data)

        pattern = r"\b\d{4}\b"
        match = re.search(pattern, response.message)
        totp_code = match.group() if match else ""

        data = ValidateOTPSerializer(phone=self.phone, otp=totp_code)
        valid = validate_otp(data)

        self.assertTrue(valid)

    def test_invalid_otp_fails(self):
        """Test invalid OTP is rejected"""
        create_otp(self.data)

        data = ValidateOTPSerializer(phone=self.phone, otp="5678")
        valid = validate_otp(data)

        self.assertFalse(valid)
