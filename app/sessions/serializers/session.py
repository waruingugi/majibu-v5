from pydantic.dataclasses import dataclass
from pydantic import BaseModel
from fastapi import Form
from typing import List

from app.core.helpers import _is_valid_category
from app.core.config import settings
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
    pass


class DuoSessionCreateSerializer(DuoSessionBaseSerializer):
    session_id: str
    party_a: str
    amount: float = settings.SESSION_AMOUNT


class DuoSessionUpdateSerializer(DuoSessionBaseSerializer):
    party_b: str | None
    status: bool | None
    winner_id: str | None


class UserSessionStatsBaseSerializer(BaseModel):
    user_id: str


class UserSessionStatsCreateSerializer(UserSessionStatsBaseSerializer):
    pass


class UserSessionStatsUpdateSerializer(UserSessionStatsBaseSerializer):
    sessions_played: int | None = 0
    total_wins: int | None = 0
    total_losess: int | None = 0
