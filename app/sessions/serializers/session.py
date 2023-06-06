from pydantic.dataclasses import dataclass
from fastapi import Form

from app.core.helpers import _is_valid_category
from app.commons.serializers.commons import BaseFormSerializer


@dataclass
class SessionCategoryFormSerializer(BaseFormSerializer):
    category: str = Form(...)

    # Validators
    _is_valid_category = _is_valid_category
