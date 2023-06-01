from pydantic.dataclasses import dataclass
from fastapi import Form
from app.commons.serializers.commons import BaseFormSerializer


@dataclass
class SessionCategoryFormSerializer(BaseFormSerializer):
    category: str = Form(...)
