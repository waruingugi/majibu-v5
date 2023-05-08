import datetime
import hashlib
import hmac
import base64

from app.core.raw_logger import logger
from app.core.config import settings


def generate_transaction_code():
    """Generate unique transaction codes"""
    logger.info("Generating unique transaction code")

    # Create uniqueness based on date
    now = datetime.datetime.now()
    msg = f"{now.month}{now.day}{now.hour}{now.minute}{now.second}{now.microsecond}".encode(
        "utf-8"
    )
    secret_key = bytes(settings.SECRET_KEY, "utf-8")
    signature = hmac.new(secret_key, msg=msg, digestmod=hashlib.sha256).digest()

    transaction_id = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    transaction_id = transaction_id.upper()  # Convert transaction_id to uppercase
    transaction_code = "".join([c for c in transaction_id if c.isalnum()])

    return f"M{transaction_code[:7]}"
