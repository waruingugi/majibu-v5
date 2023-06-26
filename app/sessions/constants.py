from enum import Enum
from typing import List


class DuoSessionStatuses(str, Enum):  # Also acts as role names
    PENDING = "PENDING"
    PAIRED = "PAIRED"
    REFUNDED = "REFUNDED"

    @classmethod
    def list_(cls) -> List:
        duo_session_statuses = {type.value for type in cls}
        return list(duo_session_statuses)
