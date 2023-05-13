from app.commons.serializers.commons import BaseFormSerializer

from fastapi import Form
from pydantic.dataclasses import dataclass
from pydantic import BaseModel, Json
from pydantic.types import PositiveFloat


@dataclass
class DepositSerializer(BaseFormSerializer):
    amount: int = Form(gt=0)


class TransactionBaseSerializer(BaseModel):
    account: str
    external_transaction_id: str
    cash_flow: str
    type: str
    status: str
    service: str
    description: str


class TransactionCreateSerializer(TransactionBaseSerializer):
    initial_balance: PositiveFloat
    final_balance: PositiveFloat
    fee: PositiveFloat
    tax: PositiveFloat
    charge: PositiveFloat
    external_response: Json | None
