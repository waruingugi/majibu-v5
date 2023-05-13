from app.commons.serializers.commons import BaseFormSerializer
from app.core.helpers import (
    _is_valid_cash_flow_state,
    _is_valid_transaction_type,
    _is_valid_transaction_status,
    _is_valid_transaction_service,
)
from app.accounts.constants import TransactionStatuses

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
    status: str = TransactionStatuses.PENDING.value
    service: str
    description: str

    # Validators
    _is_valid_cashflow_state = _is_valid_cash_flow_state
    _is_valid_transaction_type = _is_valid_transaction_type
    _is_valid_transaction_status = _is_valid_transaction_status
    _is_valid_transaction_service = _is_valid_transaction_service


class TransactionCreateSerializer(TransactionBaseSerializer):
    fee: PositiveFloat
    tax: PositiveFloat
    external_response: Json | None


class TransactionUpdateSerializer(TransactionBaseSerializer):
    pass
