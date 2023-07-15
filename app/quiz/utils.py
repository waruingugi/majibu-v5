from fastapi import Depends
from sqlalchemy.orm import Session, load_only
from typing import Optional, Sequence
from datetime import datetime, timedelta

from app.core.deps import (
    get_db,
    get_current_active_user,
)
from app.core.raw_logger import logger
from app.core.config import settings

from app.exceptions.custom import SessionExpired, LateSessionSubmission
from app.sessions.daos.session import session_dao
from app.quiz.daos.quiz import (
    result_dao,
    question_dao,
    choice_dao,
    # user_answer_dao,
)
from app.quiz.filters import QuestionFilter, ChoiceFilter
from app.quiz.models import Results
from app.users.models import User


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


class CalculateScore:
    def __init__(
        self,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_active_user),
    ) -> None:
        """Set up resources for queries"""
        logger.info("Setting up CalculateScore class...")
        self.db = db
        self.user = user

    def __call__(
        self, *, form_data: dict, result_id: str, user: Optional[User] = None
    ) -> dict | None:
        self.form_data = form_data
        self.result = result_dao.get_not_none(self.db, id=result_id)

        submitted_in_time = self.session_is_submitted_in_time()
        if submitted_in_time:
            pass

    def session_is_submitted_in_time(self) -> bool | None:
        """Assert the session answers were submitted in time"""
        buffer_time = datetime.utcnow() + timedelta(
            seconds=settings.SESSION_BUFFER_FOR_DURATION
        )
        expires_at = self.result.expires_at

        if expires_at < buffer_time:
            raise LateSessionSubmission

        return True

    def create_user_answers(self):
        no_answered_questions = 0
        for question, answer in self.form_data.items():
            no_answered_questions += 1


def table():
    for a in range(5):  # No of questions answered
        table = []
        for c in range(5):  # No of questions correct
            if c <= a:
                print(f"{c} : {a}")
                correct_score = (c / 5) * 0.8
                answered_score = (a / 5) * 0.2

                final_score = correct_score + answered_score
                table.append(final_score)
                print(table)


# init - set up user
# call - run checks
# calculate score
# Get or create useranswers
# Another function to check correct answers
# Save number of correct answers
# Save number of questions answered
# check if submitted before
# On pairing, if results is none for late submission, refund without bonus

# CorrectWeight = 0.8 (to give more weight to the number of correct answers)
# AnsweredWeight = 0.2 (to give less weight to the number of questions attempted)
# CorrectScore = (TotalCorrect / TotalQuestions) * CorrectWeight
# AnsweredScore = (TotalAnswered / TotalQuestions) * AnsweredWeight
# FinalScore = CorrectScore + AnsweredScore
