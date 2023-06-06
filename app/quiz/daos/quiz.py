from app.db.dao import CRUDDao
from app.quiz.models import Questions
from app.quiz.serializers.quiz import (
    QuestionCreateSerializer,
    QuestionUpdateSerializer,
)


class QuestionDao(
    CRUDDao[Questions, QuestionCreateSerializer, QuestionUpdateSerializer]
):
    pass


question_dao = QuestionDao(Questions)
