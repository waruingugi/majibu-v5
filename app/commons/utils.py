import uuid
from phone_gen import PhoneNumber


def generate_uuid() -> str:
    """Generate a random UUID"""
    return str(uuid.uuid4())


def random_phone(country_iso_2_code: str = "KE") -> str:
    """Generate random phone number"""
    faker_phone_number = PhoneNumber(country_iso_2_code)
    return faker_phone_number.get_mobile(full=True)
