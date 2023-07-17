from typing import Any, Dict, Union
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.dao import CRUDDao, DaoInterface
from app.core.config import settings
from app.exceptions.custom import ChoicesDAOFailedOnCreate
from app.quiz.models import Questions, Choices, Answers, Results, UserAnswers
from app.quiz.serializers.quiz import (
    QuestionCreateSerializer,
    QuestionUpdateSerializer,
    ChoiceCreateSerializer,
    ChoiceUpdateSerializer,
    AnswerCreateSerializer,
    AnswerUpdateSerializer,
    ResultCreateSerializer,
    ResultUpdateSerializer,
    UserAnswerCreateSerializer,
    UserAnswerUpdateSerializer,
)


class ResultDao(CRUDDao[Results, ResultCreateSerializer, ResultUpdateSerializer]):
    """Result DAO"""

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
    """Question DAO"""

    pass


question_dao = QuestionDao(Questions)


class ChoiceDao(CRUDDao[Choices, ChoiceCreateSerializer, ChoiceUpdateSerializer]):
    """Choice DAO"""

    def on_pre_create(
        self, db: Session, id: str, values: dict, orig_values: dict
    ) -> None:
        """Assert choices for each question do not exceed max limit"""
        choices = self.get_all(db, question_id=values["question_id"])

        if len(choices) >= settings.CHOICES_IN_QUESTION:
            raise ChoicesDAOFailedOnCreate(
                f"Could not update {values['choice_text']}. "
                f"Max choices for question {values['question_id']} reached."
            )


choice_dao = ChoiceDao(Choices)


class AnswerDao(CRUDDao[Answers, AnswerCreateSerializer, AnswerUpdateSerializer]):
    """Answer DAO"""

    def get_or_create(
        self,
        db: Session,
        obj_in: Union[AnswerCreateSerializer, AnswerUpdateSerializer],
    ) -> Answers:
        """Get or create a user answer"""
        db_obj = self.get(db, question_id=obj_in.question_id)
        if not db_obj:
            answer_data = AnswerCreateSerializer(**obj_in.dict())
            db_obj = self.create(db, obj_in=answer_data)

        return db_obj


answer_dao = AnswerDao(Answers)


class UserAnswerDao(
    CRUDDao[UserAnswers, UserAnswerCreateSerializer, UserAnswerUpdateSerializer]
):
    """UserAnswer DAO"""

    def update(
        self: Any | DaoInterface,
        db: Session,
        *,
        db_obj: UserAnswers,
        obj_in: UserAnswerUpdateSerializer | Dict[str, Any],
    ) -> None:
        """Prevent updates on UserAnswers Model. Once an instance is created, it can not be updated"""
        pass

    def get_or_create(
        self,
        db: Session,
        obj_in: Union[UserAnswerCreateSerializer, UserAnswerUpdateSerializer],
    ) -> UserAnswers:
        """Get or create a user answer"""
        db_obj = self.get(db, user_id=obj_in.user_id, question_id=obj_in.question_id)
        if not db_obj:
            user_answer_data = UserAnswerCreateSerializer(**obj_in.dict())
            db_obj = self.create(db, obj_in=user_answer_data)

        return db_obj


user_answer_dao = UserAnswerDao(UserAnswers)
