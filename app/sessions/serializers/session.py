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
    party_a: str
    session_id: str
    status: str


class DuoSessionCreateSerializer(DuoSessionBaseSerializer):
    amount: float = settings.SESSION_AMOUNT
    party_b: str | None = None
    winner_id: str | None = None


class DuoSessionUpdateSerializer(DuoSessionBaseSerializer):
    pass


class UserSessionStatsBaseSerializer(BaseModel):
    sessions_played: int | None = None
    total_wins: int | None = None
    total_losess: int | None = None


class UserSessionStatsCreateSerializer(UserSessionStatsBaseSerializer):
    user_id: str


class UserSessionStatsUpdateSerializer(UserSessionStatsBaseSerializer):
    pass


class PoolSessionStatsBaseSerializer(BaseModel):
    total_players: int | None = 0
    statistics: str | None


class PoolSessionStatsCreateSerializer(PoolSessionStatsBaseSerializer):
    pass


class PoolSessionStatsUpdateSerializer(PoolSessionStatsBaseSerializer):
    pass


class PoolCategoryStatistics(BaseModel):
    players: int | None = None
    mean_paiwise_difference: float | None = None
    threshold: float | None = None
    average_score: float | None = None
    pairing_range: float | None = None
    exp_weighted_average: float | None = None
