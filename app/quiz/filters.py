from fastapi_sqlalchemy_filter import Filter
from app.quiz.models import Results


class ResultBaseFilter(Filter):
    user__phone: str | None
    is_active: bool | None

    class Constants(Filter.Constants):
        model = Results


class ResultFilter(ResultBaseFilter):
    session__category: str | None
