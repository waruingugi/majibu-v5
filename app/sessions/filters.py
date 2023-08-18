from fastapi_sqlalchemy_filter import Filter, FilterDepends, with_prefix
from typing import List
from app.sessions.models import DuoSession, Sessions


class SessionBaseFilter(Filter):
    id: str | None = None
    category: str | None = None

    class Constants(Filter.Constants):
        model = Sessions


class SessionFilter(SessionBaseFilter):
    id__not_in: List[str] | None = None
    id__in: List[str] | None = None


class DuoSessionBaseFilter(Filter):
    party_a: str | None = None
    party_b: str | None = None
    winner: str | None = None

    class Constants(Filter.Constants):
        model = DuoSession
        search_model_fields = ["party_a", "party_b"]


class DuoSessionFilter(DuoSessionBaseFilter):
    status: str | None = None
    session_id: str | None = None
    session: SessionFilter = FilterDepends(with_prefix("session", SessionFilter))
