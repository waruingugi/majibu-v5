from fastapi import Depends
from sqlalchemy.orm import Session, load_only
from typing import Optional, Sequence
from datetime import datetime

from app.core.deps import (
    get_db,
    get_current_active_user,
)
from app.exceptions.custom import SessionExpired
from app.sessions.daos.session import session_dao
from app.quiz.daos.quiz import (
    result_dao,
    question_dao,
    choice_dao,
)
from app.quiz.filters import QuestionFilter, ChoiceFilter
from app.quiz.models import Results
from app.users.models import User
from app.core.raw_logger import logger


class GetSessionQuestions:
    def __init__(
        self,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),
    ) -> None:
        """Set up resources for queries"""
        logger.info("Setting up GetSessionQuestions class...")
        self.db = db
        self.user = user

    def __call__(self, *, result_id: str, user: Optional[User] = None) -> dict | None:
        """Compile resources to generate quiz questions and choices"""
        logger.info("Calling GetSessionQuestions class...")

        self.user = self.user if user is None else user
        result_obj = result_dao.get_not_none(
            self.db,
            id=result_id,
            user_id=self.user.id,
            load_options=[load_only(Results.session_id, Results.expires_at)],
        )

        if datetime.now() < result_obj.expires_at:
            """Accept GET requests only before expiry time"""
            self.session_obj = session_dao.get_not_none(
                self.db, id=result_obj.session_id
            )

            self.questions_obj = self.get_questions()
            self.choices_obj = self.get_choices()
            quiz = self.compose_quiz()

            return quiz

        logger.warning(
            f"{self.user.phone} requested session {result_obj.session_id} past expiry time"
        )
        raise SessionExpired

    def get_questions(self) -> Sequence:
        """Get questions"""
        logger.info(f"Getting session questions for {self.user.phone}")
        questions_obj = question_dao.search(
            self.db, search_filter=QuestionFilter(id__in=self.session_obj.questions)
        )
        return questions_obj

    def get_choices(self) -> Sequence:
        """Get choices"""
        logger.info(f"Getting session choices for {self.user.phone}")
        choices_obj = choice_dao.search(
            self.db,
            search_filter=ChoiceFilter(question_id__in=self.session_obj.questions),
        )
        return choices_obj

    def compose_quiz(self) -> list:
        """Compile questions and choices to create a quiz.
        Returned object should follow QuizObjectSerializer format"""
        logger.info(f"Compiling quiz for {self.user.phone}")
        quiz = []

        for question in self.questions_obj:
            quiz_object = {}
            choices = []
            quiz_object = {
                "id": question.id,
                "question_text": question.question_text,
            }

            for choice in self.choices_obj:
                if choice.question_id == question.id:
                    choices.append(
                        {
                            "id": choice.id,
                            "question_id": choice.question_id,
                            "choice_text": choice.choice_text,
                        }
                    )

            quiz_object["choices"] = choices
            quiz.append(quiz_object)

        return quiz


"""
[
    {
        'id': '',
        'question_text': '',
        'choices': [
            {
                'id': '',
                'choice_text': ''
            },
            {
                'id': '',
                'choice_text': ''
            }
        ]
    }
]
"""
