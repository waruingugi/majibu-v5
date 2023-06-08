from app.commons.serializers.commons import CategoryBaseSerializer
from pydantic import BaseModel


class QuestionBaseSerializer(BaseModel):
    question_text: str


class QuestionCreateSerializer(CategoryBaseSerializer):
    question_text: str


class QuestionUpdateSerializer(QuestionBaseSerializer):
    category: str | None


class ChoiceBaseSerializer(BaseModel):
    question_id: str


class ChoiceCreateSerializer(ChoiceBaseSerializer):
    choice_text: str


class ChoiceUpdateSerializer(ChoiceBaseSerializer):
    choice_text: str | None


class AnswerBaseSerializer(BaseModel):
    question_id: str


class AnswerCreateSerializer(AnswerBaseSerializer):
    choice_id: str


class AnswerUpdateSerializer(AnswerBaseSerializer):
    choice_id: str | None
