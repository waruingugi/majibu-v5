from app.core.config import settings
from app.core.raw_logger import logger

from functools import partial
import logging
import phonenumbers
import requests
from typing import Dict, Any
from tenacity import (
    Retrying,
    RetryError,
    before_log,
    stop_after_attempt,
    wait_fixed,
)


sms_max_tries = 3
wait_seconds = 2

# Define retry sms shorthand decorator.
retry_on_sms_failure = partial(
    Retrying,
    stop=stop_after_attempt(sms_max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
)()


class HostPinnacleSms:
    """Send SMS using HostPinnacle"""

    def __init__(self) -> None:
        self.user_id = settings.HOST_PINNACLE_USER_ID
        self.password = settings.HOST_PINNACLE_PASSWORD
        self.sender_id = settings.HOST_PINNACLE_SENDER_ID

        self.sms_base_url = settings.HOST_PINNACLE_SMS_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
        }
        self.sms_payload: Dict[str, str] = {
            "userid": self.user_id,
            "password": self.password,
            "mobile": "",
            "senderid": self.sender_id,
            "msg": "",
            "sendMethod": "quick",
            "msgType": "text",
            "output": "json",
            "duplicatecheck": "true",
        }

    def format_phone_number(self, phone) -> str:
        """
        HostPinnacle requires numbers without a leading + sign.
        Example: 254704302356
        """
        parsed_phone = phonenumbers.parse(phone)
        return f"{parsed_phone.country_code}{parsed_phone.national_number}"

    def send_quick_sms(self, *, recipient: str, message: str) -> Dict[str, Any]:
        """Send single quick sms"""
        self.sms_payload["mobile"] = self.format_phone_number(recipient)
        self.sms_payload["msg"] = message

        try:
            # Retry x times before failing
            for attempt in retry_on_sms_failure:
                with attempt:
                    response = requests.post(
                        url=f"{self.sms_base_url}/SMSApi/send",
                        headers=self.headers,
                        json=self.sms_payload,
                    )

                    response_json = response.json()
                    logger.info(
                        f"Sent HOST_PINNACLE SMS to {recipient}, message: {message}"
                    )
                    return {
                        "id": response_json["transactionId"],
                        "status": response_json["status"],
                        "reason": response_json["reason"],
                        "status_code": response_json["statusCode"],
                    }

        except RetryError as e:
            logger.exception(
                f"Exception {e} while sending HOST_PINNACLE SMS to {recipient}"
            )
            return {}


HPKSms = HostPinnacleSms()
