import unittest
from unittest.mock import MagicMock, patch

from app.core.tests.test_utils import random_phone
from app.notifications.utils import HPKSms


class TestHostPinnacleSms(unittest.TestCase):
    phone = random_phone()
    mock_response = MagicMock()

    def test_hpk_formats_phone_correctly(self):
        """Test the func ´format_phone_number´ returns correct format"""
        response = HPKSms.format_phone_number(self.phone)
        assert response == self.phone[1:]

    def test_make_send_payment_request_raises_an_error(self):
        with patch("app.notifications.utils.requests") as mock_request:
            mock_request.post.side_effect = Exception("Test Exception raised!")
            response = HPKSms.send_quick_sms(recipient=self.phone, message="test")
            self.assertEqual({}, response)

    @patch("app.notifications.utils.requests")
    def test_hpk_sms_returns_successful_response(self, mock_requests):
        # Full succesfull response
        # successful_response = {
        #     "status": "success",
        #     "mobile": self.phone[1:],
        #     "invalidMobile": "",
        #     "transactionId": "8022707474479533778",
        #     "statusCode": "200",
        #     "reason": "success",
        #     "msgId": ""
        # }
        mock_response = {
            "transactionId": "8022707474479533778",
            "statusCode": "200",
            "status": "success",
            "reason": "success",
        }

        self.mock_response.json.return_value = mock_response
        mock_requests.post.return_value = self.mock_response
        response = HPKSms.send_quick_sms(recipient=self.phone, message="test")

        successful_response = {
            "id": mock_response["transactionId"],
            "status_code": "200",
            "status": "success",
            "reason": "success",
        }

        assert response == successful_response
