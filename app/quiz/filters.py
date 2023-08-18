from fastapi_sqlalchemy_filter import Filter, FilterDepends, with_prefix
from typing import List

from app.quiz.models import Results, Questions, Choices
from app.sessions.filters import SessionFilter


class ResultBaseFilter(Filter):
    user__id: str | None = None
    is_active: bool | None = None

    class Constants(Filter.Constants):
        model = Results


class ResultFilter(ResultBaseFilter):
    session: SessionFilter = FilterDepends(with_prefix("session", SessionFilter))


class QuestionBaseFilter(Filter):
    category: str | None = None
    question_text_ilike: str | None = None

    class Constants(Filter.Constants):
        model = Questions


class QuestionFilter(QuestionBaseFilter):
    id__in: List[str] | None = None


class ChoiceBaseFilter(Filter):
    question_id: str | None = None

    class Constants(Filter.Constants):
        model = Choices


class ChoiceFilter(ChoiceBaseFilter):
    choice_text: str | None = None
    question_id__in: List[str] | None = None
