from app.exceptions.custom import HttpErrorException, InvalidEnumValue
from app.accounts.constants import (
    TransactionCashFlow,
    TransactionType,
    TransactionStatuses,
    TransactionService,
)
from app.errors.custom import ErrorCodes
from app.core.raw_logger import logger
from app.core.config import settings

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
    return value_exists_in_enum(value, TransactionType)


_is_valid_transaction_type = validator("type", pre=True, allow_reuse=True)(
    is_valid_transaction_type
)


def is_valid_transaction_status(value: str):
    return value_exists_in_enum(value, TransactionStatuses)


_is_valid_transaction_status = validator("status", pre=True, allow_reuse=True)(
    is_valid_transaction_status
)


def is_valid_transaction_service(value: str):
    return value_exists_in_enum(value, TransactionService)


_is_valid_transaction_service = validator("service", pre=True, allow_reuse=True)(
    is_valid_transaction_service
)
