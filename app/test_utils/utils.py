from phone_gen import PhoneNumber

from typing import Optional


def random_phone(country_iso_2_code: Optional[str] = "KE") -> str:
    faker_phone_number = PhoneNumber(country_iso_2_code)
    return faker_phone_number.get_mobile(full=True)