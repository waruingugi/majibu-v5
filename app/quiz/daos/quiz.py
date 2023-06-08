from app.db.dao import CRUDDao
from app.quiz.models import Questions, Choices, Answers
from app.quiz.serializers.quiz import (
    QuestionCreateSerializer,
    QuestionUpdateSerializer,
    ChoiceCreateSerializer,
    ChoiceUpdateSerializer,
    AnswerCreateSerializer,
    AnswerUpdateSerializer,
)


class QuestionDao(
    CRUDDao[Questions, QuestionCreateSerializer, QuestionUpdateSerializer]
):
    pass


question_dao = QuestionDao(Questions)


class ChoiceDao(CRUDDao[Choices, ChoiceCreateSerializer, ChoiceUpdateSerializer]):
    pass


choice_dao = ChoiceDao(Choices)


class AnswerDao(CRUDDao[Answers, AnswerCreateSerializer, AnswerUpdateSerializer]):
    pass


answer_dao = AnswerDao(Answers)
