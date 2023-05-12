from pydantic import root_validator, BaseModel
from pydantic.dataclasses import dataclass
from fastapi import Form

from app.core.helpers import (
    validate_phone_number,
    _standardize_phone_to_required_format,
)
from app.core.raw_logger import logger
from app.core.config import settings
from app.commons.serializers.commons import BaseFormSerializer


@dataclass
class FormatPhoneSerializer(BaseFormSerializer):
    phone: str = Form(...)

    _standardize_phone_to_required_format = _standardize_phone_to_required_format

    @root_validator(skip_on_failure=False)
    def validate_form_data(cls, values):
        """Run form validations here"""
        field_errors = values["field_errors"]

        try:
            validate_phone_number(values["phone"])

        except Exception as e:
            field_errors.append(e.error_message)  # type: ignore
            logger.exception(
                f"An exception occured in the form validation: {e.error_message}"  # type: ignore
            )
        finally:
            values["field_errors"] = field_errors
            return values


@dataclass
class OTPSerializer(BaseFormSerializer):
    otp: str = Form(max_length=settings.TOTP_LENGTH, min_length=settings.TOTP_LENGTH)


class LitePhoneSerializer(BaseModel):
    phone: str


class CreateOTPSerializer(LitePhoneSerializer):
    ...


class ValidateOTPSerializer(LitePhoneSerializer):
    otp: str
