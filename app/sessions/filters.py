from fastapi_sqlalchemy_filter import Filter
from typing import List
from app.sessions.models import DuoSession, Sessions


class SessionBaseFilter(Filter):
    id: str | None
    category: str | None

    class Constants(Filter.Constants):
        model = Sessions


class SessionFilter(SessionBaseFilter):
    id__not_in: List[str] | None


class DuoSessionBaseFilter(Filter):
    party_a: str | None
    party_b: str | None
    winner: str | None

    class Constants(Filter.Constants):
        model = DuoSession
        search_model_fields = ["party_a", "party_b", "winner"]


class DuoSessionFilter(DuoSessionBaseFilter):
    status: str | None
    session__category: str | None
    session__id__in: List[str] | None
    session__id__not_in: List[str] | None
