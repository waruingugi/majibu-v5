from app.core.helpers import validate_phone_number, get_mpesa_client_ip_address
from app.accounts.constants import MPESA_WHITE_LISTED_IPS
from app.exceptions.custom import HttpErrorException
import random
import pytest


class TestPhoneValidation:
    phone = "+254704845040"

    def test_correct_phone_format_validates(self):
        result = validate_phone_number(TestPhoneValidation.phone)
        assert result == TestPhoneValidation.phone

    def test_raise_error_for_invalid_country(self):
        for i in range(1, 4):
            with pytest.raises(HttpErrorException):
                phone = TestPhoneValidation.phone[i:]
                validate_phone_number(phone)


def test_get_mpesa_client_ip_address_returns_correct_value() -> None:
    """Test the function returns the first valid IP address"""
    random_mpesa_address = random.choice(MPESA_WHITE_LISTED_IPS)

    ip_addresses_x = ["10.14.13.14", "10.195.4.29", "10.14.6.10", random_mpesa_address]
    random_ip_addresses_x = ", ".join(ip_addresses_x)

    ip_addresses_y = ["10.14.13.14", "10.195.4.29", "10.14.6.10", random_mpesa_address]
    random_ip_addresses_y = ", ".join(ip_addresses_y)

    mpesa_ip_address_x = get_mpesa_client_ip_address(
        random.choice(ip_addresses_x), random_ip_addresses_x
    )
    mpesa_ip_address_y = get_mpesa_client_ip_address(
        random.choice(ip_addresses_y), random_ip_addresses_y
    )

    assert mpesa_ip_address_x == random_mpesa_address
    assert mpesa_ip_address_y == random_mpesa_address


def test_get_mpesa_client_ip_address_returns_host_ip_address() -> None:
    """Test that the function reverts to request.client.host IP address if a valid
    IP address in not found or when the x-forwarded-for value does not exist in the header"""
    random_ip_addresses = ", ".join(["10.14.13.14", "10.195.4.29", "10.14.6.10"])
    mpesa_ip_address = get_mpesa_client_ip_address(
        random.choice(random_ip_addresses), None
    )

    assert mpesa_ip_address is not None
