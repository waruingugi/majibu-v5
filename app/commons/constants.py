from enum import Enum
from typing import List


class Categories(Enum):
    BIBLE = "BIBLE"
    FOOTBALL = "FOOTBALL"

    @classmethod
    def list_(cls) -> List:
        categories = {category.value for category in cls}
        return list(categories)
