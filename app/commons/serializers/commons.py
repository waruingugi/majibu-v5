from pydantic.dataclasses import dataclass
from typing import List


@dataclass
class BaseFormSerializer:
    field_errors: List[str]

    def is_valid(self):
        return True if not self.field_errors else False
