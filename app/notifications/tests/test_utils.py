import unittest
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.notifications.utils import HPKSms, MobiTechSms


class TestHostPinnacleSms(unittest.TestCase):
    phone = settings.SUPERUSER_PHONE
    mock_response = MagicMock()

    def test_hpk_formats_phone_correctly(self):
        """Test the func ´format_phone_number´ returns correct format"""
        response = HPKSms.format_phone_number(self.phone)
        assert response == self.phone[1:]

    def test_send_payment_request_raises_an_error(self):
        with patch("app.notifications.utils.requests") as mock_request:
            mock_request.post.side_effect = Exception("Test Exception raised!")
            response = HPKSms.send_quick_sms(phone=self.phone, message="test")
            self.assertEqual({}, response)

    @patch("app.notifications.utils.requests")
    def test_hpk_sms_returns_successful_response(self, mock_requests):
        mock_request_response = {
            "status": "success",
            "mobile": self.phone[1:],
            "invalidMobile": "",
            "transactionId": "8022707474479533778",
            "statusCode": "200",
            "reason": "success",
            "msgId": "",
        }

        self.mock_response.json.return_value = mock_request_response
        mock_requests.post.return_value = self.mock_response
        response = HPKSms.send_quick_sms(phone=self.phone, message="test")

        successful_response = {
            "status_code": "200",
            "status": "success",
            "reason": "success",
        }

        assert response == successful_response


class TestMobiTechTechnologiesSms(unittest.TestCase):
    phone = settings.SUPERUSER_PHONE
    mock_response = MagicMock()

    def test_send_payment_request_raises_an_error(self):
        with patch("app.notifications.utils.requests") as mock_request:
            mock_request.post.side_effect = Exception("Test Exception raised!")
            response = MobiTechSms.send_quick_sms(phone=self.phone, message="test")
            self.assertEqual({}, response)

    @patch("app.notifications.utils.requests")
    def test_mobitech_sms_returns_successful_response(self, mock_requests):
        mock_request_response = [
            {
                "status_code": "1000",
                "status_desc": "Success",
                "message_id": 70055777,
                "mobile_number": "254702739804",
                "network_id": "1",
                "message_cost": 0.1,
                "credit_balance": 5165.7,
            }
        ]

        self.mock_response.json.return_value = mock_request_response
        mock_requests.post.return_value = self.mock_response
        response = MobiTechSms.send_quick_sms(phone=self.phone, message="test")

        successful_response = {
            "status_code": "1000",
            "status": "success",
            "reason": "Success",
        }

        assert response == successful_response
