from pydantic import validator, root_validator
from pydantic.dataclasses import dataclass
from fastapi import Form
from typing import List
import phonenumbers

from app.core.helpers import validate_phone_number
from app.core.raw_logger import logger
from app.core.config import settings


@dataclass
class BaseFormSerializer:
    field_errors: List[str] | None

    def is_valid(self):
        return True if not self.field_errors else False


@dataclass
class FormatPhoneSerializer(BaseFormSerializer):
    phone: str = Form(...)

    @validator("phone", pre=True)
    def standardize_phone_to_required_format(cls, value):
        """Change phone number input to international format: +254702005008"""
        parsed_phone = phonenumbers.parse(value, settings.DEFAULT_COUNTRY_ISO2_CODE)
        return phonenumbers.format_number(
            parsed_phone, phonenumbers.PhoneNumberFormat.E164
        )

    @root_validator(skip_on_failure=False)
    def validate_form_data(cls, values):
        """Run form validations here"""
        field_errors = values["field_errors"]

        try:
            validate_phone_number(values["phone"])
        except Exception as e:
            field_errors.append(e.error_message)  # type: ignore
            logger.info(f"An exception occured in the form validation: {e.error_message}")  # type: ignore
        finally:
            values["field_errors"] = field_errors
            return values

    # def is_valid(self):
    #     """Do form validations here"""
    #     self.errors: List = []
    #     try:
    #         validate_phone_number(self.phone)
    #     except Exception as e:
    #         self.errors.append(e.error_message) # type: ignore
    #         logger.info(f"An exception occured in the form validation: {e.error_message}") # type: ignore
    #     finally:
    #         return True if not self.errors else False
