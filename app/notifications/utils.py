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

    def send_quick_sms(self, *, phone: str, message: str) -> Dict | None:
        """Send single quick sms"""
        self.sms_payload["mobile"] = self.format_phone_number(phone)
        self.sms_payload["msg"] = message

        try:
            # Retry x times before failing
            for attempt in retry_on_sms_failure:
                with attempt:
                    logger.info(
                        f"Sending HostPinnacle SMS to {phone}, message: {message}"
                    )
                    response = requests.post(
                        url=f"{self.sms_base_url}/SMSApi/send",
                        headers=self.headers,
                        json=self.sms_payload,
                    )

                    response_json = response.json()
                    logger.info(f"HostPinnalce response: {response_json}")

                    return {
                        "status": response_json["status"],
                        "reason": response_json["reason"],
                        "status_code": response_json["statusCode"],
                    }

        except RetryError as e:
            logger.exception(f"Exception {e} while sending HostPinnacle SMS to {phone}")
            return {}


HPKSms = HostPinnacleSms()


class MobiTechTechnologiesSms:
    """Send SMS using Mobitech"""

    def __init__(self) -> None:
        self.api_key = settings.MOBI_TECH_API_KEY
        self.sender_name = settings.MOBI_TECH_SENDER_NAME

        self.sms_base_url = settings.MOBI_TECH_SMS_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "h_api_key": self.api_key,
        }
        self.sms_payload: Dict[str, Any] = {
            "mobile": "",
            "response_type": "json",
            "sender_name": "23107",
            "service_id": 0,
            "message": "",
        }

    def send_quick_sms(self, *, phone: str, message: str) -> Dict | None:
        """Send single quick sms"""
        self.sms_payload["mobile"] = phone
        self.sms_payload["message"] = message

        try:
            # Retry x times before failing
            for attempt in retry_on_sms_failure:
                with attempt:
                    logger.info(f"Sending MobiTech SMS to {phone}, message: {message}")

                    response = requests.post(
                        url=f"{self.sms_base_url}/sms/sendsms",
                        headers=self.headers,
                        json=self.sms_payload,
                    )

                    response_json = response.json()[0]
                    logger.info(f"MobiTech response: {response_json}")

                    return {
                        "status": (
                            "success"
                            if response_json["status_code"] == "1000"
                            else response_json["status_code"]
                        ),
                        "reason": response_json["status_desc"],
                        "status_code": response_json["status_code"],
                    }

        except RetryError as e:
            logger.exception(f"Exception {e} while sending MobiTech SMS to {phone}")
            return {}


MobiTechSms = MobiTechTechnologiesSms()
