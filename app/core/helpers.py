from app.exceptions.custom import HttpErrorException
from app.errors.custom import ErrorCodes

from http import HTTPStatus
from phonenumbers import parse as parse_phone_number
from phonenumbers import (
    NumberParseException,
    PhoneNumberType,
    is_valid_number,
    number_type,
)
from pydantic import validator

PHONE_NUMBER_TYPES = PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE


def validate_phone_number(phone: str) -> str:
    """Validate str can be parsed into phone number"""
    invalid_phone_number_exception = HttpErrorException(
        status_code=HTTPStatus.BAD_REQUEST,
        error_code=ErrorCodes.INVALID_PHONENUMBER.name,
        error_message=ErrorCodes.INVALID_PHONENUMBER.value.format(phone),
    )
    try:
        parsed_phone = parse_phone_number(phone)
    except NumberParseException:
        raise invalid_phone_number_exception

    if number_type(parsed_phone) not in PHONE_NUMBER_TYPES or not is_valid_number(
        parsed_phone
    ):
        raise invalid_phone_number_exception

    return phone


_validate_phone_number = validator("phone", pre=True, allow_reuse=True)(
    validate_phone_number
)
