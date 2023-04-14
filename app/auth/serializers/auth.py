from pydantic import BaseModel
from app.core.helpers import _validate_phone_number


class LoginSerializer(BaseModel):
    phone: str


class ValidatePhoneNumber(BaseModel):
    phone: str

    _validate_phone_number = _validate_phone_number
