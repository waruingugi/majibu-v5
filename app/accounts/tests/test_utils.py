import unittest
from unittest.mock import MagicMock, patch

from app.accounts.utils import get_mpesa_access_token
from app.core.config import redis


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
