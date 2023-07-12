from app.commons.serializers.commons import CategoryBaseSerializer

from pydantic import BaseModel
from typing import List


class QuestionBaseSerializer(BaseModel):
    question_text: str


class QuestionCreateSerializer(CategoryBaseSerializer):
    question_text: str


class QuestionReadSerializer(QuestionBaseSerializer):
    id: str


class QuestionUpdateSerializer(QuestionBaseSerializer):
    category: str | None


class ChoiceBaseSerializer(BaseModel):
    question_id: str


class ChoiceCreateSerializer(ChoiceBaseSerializer):
    choice_text: str


class ChoiceReadSerializer(ChoiceCreateSerializer):
    pass


class ChoiceUpdateSerializer(ChoiceBaseSerializer):
    choice_text: str | None


class ChoiceInDBSerializer(ChoiceReadSerializer):
    id: str


class AnswerBaseSerializer(BaseModel):
    question_id: str


class AnswerCreateSerializer(AnswerBaseSerializer):
    choice_id: str


class AnswerUpdateSerializer(AnswerBaseSerializer):
    choice_id: str | None


class ResultBaseSerializer(BaseModel):
    user_id: str
    session_id: str


class ResultCreateSerializer(ResultBaseSerializer):
    pass
    # percentage: float = 0.0
    # total_answered: int = 0
    # speed: float = 0.0
    # time_taken: float = 0.0
    # score: float = 0.0


class ResultUpdateSerializer(BaseModel):
    percentage: float = 0.0
    total_answered: int = 0
    speed: float = 0.0
    time_taken: float = 0.0
    score: float = 0.0


class QuizObjectSerializer(QuestionReadSerializer):
    choices: List[ChoiceInDBSerializer]
