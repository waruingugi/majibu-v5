from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.dao import CRUDDao
from app.core.config import settings
from app.quiz.models import Questions, Choices, Answers, Results
from app.quiz.serializers.quiz import (
    QuestionCreateSerializer,
    QuestionUpdateSerializer,
    ChoiceCreateSerializer,
    ChoiceUpdateSerializer,
    AnswerCreateSerializer,
    AnswerUpdateSerializer,
    ResultCreateSerializer,
    ResultUpdateSerializer,
)


class ResultDao(CRUDDao[Results, ResultCreateSerializer, ResultUpdateSerializer]):
    def create(self, db: Session, *, obj_in: ResultCreateSerializer) -> Results:
        """Assign the expires_at variable a value on creating instance"""
        session_start_time = datetime.now()
        session_end_time = session_start_time + timedelta(
            seconds=settings.SESSION_DURATION
        )

        create_result_data = obj_in.dict()
        create_result_data["expires_at"] = session_end_time

        db_obj = Results(**create_result_data)

        db.add(db_obj)
        db.commit()

        db_obj = self.get_not_none(
            db,
            user_id=db_obj.user_id,
            session_id=db_obj.session_id,
        )
        self.on_post_create(db, db_obj)

        return db_obj


result_dao = ResultDao(Results)


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
