from app.commons.serializers.commons import BaseFormSerializer

from fastapi import Form
from pydantic.dataclasses import dataclass


@dataclass
class DepositSerializer(BaseFormSerializer):
    amount: int = Form(max_length=4, min_length=1)
