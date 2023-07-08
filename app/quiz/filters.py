from fastapi_sqlalchemy_filter import Filter
from typing import List

from app.quiz.models import Results, Questions, Choices


class ResultBaseFilter(Filter):
    user__phone: str | None
    is_active: bool | None

    class Constants(Filter.Constants):
        model = Results


class ResultFilter(ResultBaseFilter):
    session__category: str | None


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
