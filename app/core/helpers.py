from app.exceptions.custom import HttpErrorException
from app.errors.custom import ErrorCodes
from app.core.raw_logger import logger

from http import HTTPStatus
from phonenumbers import parse as parse_phone_number
from phonenumbers import (
    NumberParseException,
    PhoneNumberType,
    is_valid_number,
    number_type,
)
from pydantic import validator
from hashlib import md5

PHONE_NUMBER_TYPES = PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE


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


def md5_hash(value: str) -> str:
    """Convert string value into hash"""
    return md5(value.encode()).hexdigest()
