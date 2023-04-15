from phone_gen import PhoneNumber


def random_phone(country_iso_2_code: str = "KE") -> str:
    faker_phone_number = PhoneNumber(country_iso_2_code)
    return faker_phone_number.get_mobile(full=True)
