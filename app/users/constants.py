from enum import Enum
from typing import List


class UserTypes(str, Enum):  # Also acts as role names
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    PLAYER = "PLAYER"

    @classmethod
    def list_(cls) -> List:
        user_types = {type.value for type in cls}
        return list(user_types)
