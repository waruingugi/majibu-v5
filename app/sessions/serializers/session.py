from pydantic.dataclasses import dataclass
from pydantic import BaseModel
from fastapi import Form
from typing import List

from app.core.helpers import _is_valid_category
from app.commons.serializers.commons import BaseFormSerializer


@dataclass
class SessionCategoryFormSerializer(BaseFormSerializer):
    category: str = Form(...)

    # Validators
    _is_valid_category = _is_valid_category


class SesssionBaseSerializer(BaseModel):
    category: str


class SessionCreateSerializer(SesssionBaseSerializer):
    questions: List[str]


class SessionUpdateSerializer(SesssionBaseSerializer):
    category: str | None
    questions: List[str] | None


class DuoSessionBaseSerializer(BaseModel):
    party_a: str
    session_id: str


class DuoSessionCreateSerializer(DuoSessionBaseSerializer):
    amount: float


class DuoSessionUpdateSerializer(DuoSessionBaseSerializer):
    party_b: str | None
    status: bool | None
    winner_id: str | None
