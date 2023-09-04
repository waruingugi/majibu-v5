from app.exceptions.custom import HttpErrorException, InvalidEnumValue
from app.accounts.constants import (
    TransactionCashFlow,
    TransactionTypes,
    TransactionStatuses,
    TransactionServices,
)
from app.commons.constants import Categories
from app.errors.custom import ErrorCodes
from app.core.raw_logger import logger
from app.core.config import settings

import ipaddress
from http import HTTPStatus
from phonenumbers import parse as parse_phone_number
from phonenumbers import (
    NumberParseException,
    PhoneNumberType,
    is_valid_number,
    number_type,
    parse,
    format_number,
    PhoneNumberFormat,
)
from pydantic import validator
from typing import List
from hashlib import md5, sha256
from datetime import datetime
import hmac
import base64

PHONE_NUMBER_TYPES = PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE


def md5_hash(value: str) -> str:
    """Convert string value into hash"""
    return md5(value.encode()).hexdigest()


def generate_transaction_code():
    """Generate unique transaction codes"""
    logger.info("Generating unique transaction code")

    # Create uniqueness based on date
    now = datetime.now()
    msg = f"{now.month}{now.day}{now.hour}{now.minute}{now.second}{now.microsecond}".encode(
        "utf-8"
    )
    secret_key = bytes(settings.SECRET_KEY, "utf-8")
    signature = hmac.new(secret_key, msg=msg, digestmod=sha256).digest()

    transaction_id = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    transaction_id = transaction_id.upper()  # Convert transaction_id to uppercase
    transaction_code = "".join([c for c in transaction_id if c.isalnum()])

    return f"M{transaction_code[:8]}"


def validate_phone_number(phone: str) -> str:
    """Validate str can be parsed into phone number"""
    logger.info(f"Validating phone number {phone}")

    invalid_phone_number_exception = HttpErrorException(
        status_code=HTTPStatus.BAD_REQUEST,
        error_code=ErrorCodes.INVALID_PHONENUMBER.name,
        error_message=ErrorCodes.INVALID_PHONENUMBER.value.format(phone),
    )
    try:
        parsed_phone = parse_phone_number(phone)
    except NumberParseException:
        logger.info(f"Failed to parse phone number {phone}")
        raise invalid_phone_number_exception

    if number_type(parsed_phone) not in PHONE_NUMBER_TYPES or not is_valid_number(
        parsed_phone
    ):
        logger.info(f"Invalid phone number {phone}")
        raise invalid_phone_number_exception

    return phone


_validate_phone_number = validator("phone", pre=True, allow_reuse=True)(
    validate_phone_number
)


def standardize_phone_to_required_format(phone: str):
    """Change phone number input to international format: +254702005008"""
    try:
        parsed_phone = parse(phone, settings.DEFAULT_COUNTRY_ISO2_CODE)

        return format_number(parsed_phone, PhoneNumberFormat.E164)
    except Exception as e:
        logger.exception(f"Exception {e} occured while standardizing phone {phone}")
        return phone


_standardize_phone_to_required_format = validator("phone", pre=True, allow_reuse=True)(
    standardize_phone_to_required_format
)


def value_exists_in_enum(value, enum_state):
    """Validate value is in Enum state"""
    states = [type.value for type in enum_state.__members__.values()]
    if value not in states:
        raise InvalidEnumValue(f"The {value} value does not exist in {enum_state}")
    return value


def is_valid_cash_flow_state(value: str):
    return value_exists_in_enum(value, TransactionCashFlow)


_is_valid_cash_flow_state = validator("cash_flow", pre=True, allow_reuse=True)(
    is_valid_cash_flow_state
)


def is_valid_transaction_type(value: str):
    return value_exists_in_enum(value, TransactionTypes)


_is_valid_transaction_type = validator("type", pre=True, allow_reuse=True)(
    is_valid_transaction_type
)


def is_valid_transaction_status(value: str):
    return value_exists_in_enum(value, TransactionStatuses)


_is_valid_transaction_status = validator("status", pre=True, allow_reuse=True)(
    is_valid_transaction_status
)


def is_valid_transaction_service(value: str) -> str | None:
    return value_exists_in_enum(value, TransactionServices)


_is_valid_transaction_service = validator("service", pre=True, allow_reuse=True)(
    is_valid_transaction_service
)


def is_valid_category(value: str) -> str | None:
    return value_exists_in_enum(value, Categories)


_is_valid_category = validator("category", pre=True, allow_reuse=True)(
    is_valid_category
)


def format_mpesa_receiver_details(receiver_string):
    parts = receiver_string.split(" - ")
    phone_number = f"+{parts[0].strip()}"
    full_name = parts[1].strip()
    return phone_number, full_name


def format_mpesa_result_params_to_dict(result_parameters):
    """Format value in serializer into a key - value dict"""
    result_dict = {}
    for serialized_item in result_parameters:
        item = serialized_item.dict()
        result_dict[item["Key"]] = item["Value"]

    return result_dict


def format_b2c_mpesa_date_to_timestamp(date_string) -> datetime:
    datetime_obj = datetime.strptime(date_string, "%d.%m.%Y %H:%M:%S")
    return datetime_obj


def convert_list_to_string(list_value: List[str]) -> str:
    """Convert list to string"""
    return ", ".join(map(str, set(list_value))) if list_value else ""


def mask_phone_number(phone_number: str) -> str:
    """Mask a phone number. Example result: +254703xxx675"""
    masked_number = phone_number[:7] + "xxx" + phone_number[10:]
    return masked_number


def get_mpesa_client_ip_address(host_ip: str, x_forwarded_for: str | None):
    """
    Selects the first valid and non-private IP address from the leftmost in
    the X-Forwarded-For header based on this approach:
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For#selecting_an_ip_address

    Function is required because M-Pesa sometimes uses a proxy and we need the
    original IP address
    """
    logger.info("Fetching valid M-Pesa IP address...")

    # If no x_forwarded_for header, revert to the host IP address
    if x_forwarded_for is not None:
        ip_address_list = [ip.strip() for ip in x_forwarded_for.split(",")]

        # Iterate through the IPs from left to right
        for ip in ip_address_list:
            try:
                # Parse the IP address and check if it's private
                ip = ipaddress.ip_address(ip)
                if not ip.is_private:
                    return str(ip)
            except ValueError:
                # Invalid IP address, continue to the next one
                continue

    return host_ip
