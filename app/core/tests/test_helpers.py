from app.core.helpers import validate_phone_number
from app.exceptions.custom import HttpErrorException
import pytest


class TestPhoneValidation:
    phone = "+254704845040"

    def test_correct_phone_format_validates(self):
        result = validate_phone_number(TestPhoneValidation.phone)
        assert result == TestPhoneValidation.phone

    def test_raise_error_for_invalid_country(self, subtests):
        for i in range(1, 4):
            with pytest.raises(HttpErrorException):
                phone = TestPhoneValidation.phone[i:]
                validate_phone_number(phone)
