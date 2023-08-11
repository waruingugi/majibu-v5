from enum import Enum
from typing import List


class DuoSessionStatuses(str, Enum):  # Also acts as role names
    PAIRED = "PAIRED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"

    @classmethod
    def list_(cls) -> List:
        duo_session_statuses = {type.value for type in cls}
        return list(duo_session_statuses)
