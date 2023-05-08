from app.commons.serializers.commons import BaseFormSerializer

from fastapi import Form
from pydantic.dataclasses import dataclass


@dataclass
class DepositSerializer(BaseFormSerializer):
    amount: int = Form(gt=0)
