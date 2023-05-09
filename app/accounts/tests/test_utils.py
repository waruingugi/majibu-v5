import unittest
from unittest.mock import MagicMock, patch

from app.accounts.utils import get_mpesa_access_token, initiate_mpesa_stkpush_payment
from app.core.config import redis, settings
from app.accounts.constants import MpesaAccountTypes
from app.exceptions.custom import STKPushFailed


class TestMpesaSTKPush(unittest.TestCase):
    mock_response = MagicMock()

    @classmethod
    def setUp(cls):
        redis.flushall()  # Flush all values from redis

    @classmethod
    def tearDown(cls):
        redis.flushall()  # Flush all values from redis

    @patch("app.accounts.utils.requests")
    def test_get_mpesa_access_token(self, mock_requests):
        expected_access_token = "c9SQxWWhmdVRlyh0zh8gZDTkubVF"
        self.mock_response.json.return_value = {
            "access_token": expected_access_token,
            "expires_in": "3599",
        }
        mock_requests.get.return_value = self.mock_response

        access_token = get_mpesa_access_token()
        assert access_token == expected_access_token

    @patch("app.accounts.utils.requests")
    def test_get_mpesa_access_token_is_set_in_redis(self, mock_requests):
        expected_access_token = "c9SQxWWhmdVRlyh0zh8gZDTkubVF"
        self.mock_response.json.return_value = {
            "access_token": expected_access_token,
            "expires_in": "3599",
        }
        mock_requests.get.return_value = self.mock_response

        get_mpesa_access_token()  # Call first time
        access_token = get_mpesa_access_token()  # Second call
        assert access_token == expected_access_token
        assert mock_requests.get.call_count == 1

    @patch("app.accounts.utils.get_mpesa_access_token")
    def test_initiate_mpesa_stkpush_payment(self, mock_get_mpesa_access_token):
        mock_get_mpesa_access_token.return_value = "c9SQxWWhmdVRlyh0zh8gZDTkubVF"

        with patch("app.accounts.utils.requests") as mock_requests:
            self.mock_response.json.return_value = {
                "MerchantRequestID": "29115-34620561-1",
                "CheckoutRequestID": "ws_CO_191220191020363925",
                "ResponseCode": "0",
                "ResponseDescription": "Success. Request accepted for processing",
                "CustomerMessage": "Success. Request accepted for processing",
            }
            mock_requests.post.return_value = self.mock_response

            response = initiate_mpesa_stkpush_payment(
                phone_number=settings.SUPERUSER_PHONE,
                amount=1,
                business_short_code=settings.MPESA_BUSINESS_SHORT_CODE,
                party_b=settings.MPESA_BUSINESS_SHORT_CODE,
                passkey=settings.MPESA_PASS_KEY,
                transaction_type=MpesaAccountTypes.PAYBILL.value,
                callback_url=settings.MPESA_CALLBACK_URL,
                reference=settings.SUPERUSER_PHONE,
                description="",
            )

            assert response == self.mock_response.json()

    @patch("app.accounts.utils.get_mpesa_access_token")
    @patch("app.accounts.utils.requests")
    def test_initiate_mpesa_stkpush_payment_raises_exception(
        self, mock_get_mpesa_access_token, mock_requests
    ):
        mock_get_mpesa_access_token.return_value = "c9SQxWWhmdVRlyh0zh8gZDTkubVF"

        with self.assertRaises(Exception):
            mock_requests.side_effect = STKPushFailed

            initiate_mpesa_stkpush_payment(
                phone_number=settings.SUPERUSER_PHONE,
                amount=1,
                business_short_code=settings.MPESA_BUSINESS_SHORT_CODE,
                party_b=settings.MPESA_BUSINESS_SHORT_CODE,
                passkey=settings.MPESA_PASS_KEY,
                transaction_type=MpesaAccountTypes.PAYBILL.value,
                callback_url=settings.MPESA_CALLBACK_URL,
                reference=settings.SUPERUSER_PHONE,
                description="",
            )
