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
    user_answer_dao,
    answer_dao,
)
from app.quiz.filters import QuestionFilter, ChoiceFilter
from app.quiz.serializers.quiz import (
    UserAnswerCreateSerializer,
    ResultUpdateSerializer,
)
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
        self.user = self.user if user is None else user
        self.result = result_dao.get_not_none(self.db, id=result_id)

        submitted_in_time = self.session_is_submitted_in_time()
        if submitted_in_time:
            total_answered = self.create_user_answers()
            total_correct = self.get_total_correct_questions()

            total_answered_score = self.calculate_total_answered_score(total_answered)
            total_correct_answered_score = self.calculate_correct_answered_score(
                total_correct
            )

            final_score = self.calculate_final_score(
                total_answered_score, total_correct_answered_score
            )

            result_in = ResultUpdateSerializer(
                total_correct=total_correct,
                total_answered=total_answered,
                score=final_score,
            )
            result_dao.update(self.db, db_obj=self.result, obj_in=result_in)

    def session_is_submitted_in_time(self) -> bool | None:
        """Assert the session answers were submitted in time"""
        buffer_time = datetime.utcnow() + timedelta(
            seconds=settings.SESSION_BUFFER_FOR_DURATION
        )
        expires_at = self.result.expires_at

        if expires_at < buffer_time:
            raise LateSessionSubmission

        return True

    def create_user_answers(self) -> int:
        """Save user answers to UserAnswers model"""
        total_answered = 0
        for question_id, choice_id in self.form_data.items():
            total_answered += 1
            user_answer_in = UserAnswerCreateSerializer(
                user_id=self.user.id,
                question_id=question_id,
                session_id=self.result.session_id,
                choice_id=choice_id,
            )

            user_answer_dao.get_or_create(self.db, obj_in=user_answer_in)

        return total_answered

    def get_total_correct_questions(self) -> int:
        """Calculate total questions user got correct"""
        total_correct = 0
        for question_id, choice_id in self.form_data.items():
            answer = answer_dao.get_not_none(self.db, question_id=question_id)

            if choice_id == answer.choice_id:
                total_correct += 1

        return total_correct

    def calculate_total_answered_score(self, total_answered: int) -> float:
        """Calculate total answered score"""
        total_answered_score = settings.SESSION_TOTAL_ANSWERED_WEIGHT * (
            total_answered / settings.QUESTIONS_IN_SESSION
        )

        return total_answered_score

    def calculate_correct_answered_score(self, total_correct) -> float:
        """Calculate total correct score"""
        total_correct_score = settings.SESSION_CORRECT_ANSWERED_WEIGHT * (
            total_correct / settings.QUESTIONS_IN_SESSION
        )

        return total_correct_score

    def calculate_final_score(
        self, total_answered_score: float, total_correct_score: float
    ) -> float:
        """Calculate final score"""
        return total_answered_score + total_correct_score


# init - set up user
# call - run checks
# calculate score
# Get or create useranswers
# Another function to check correct answers
# Save number of correct answers
# Save number of questions answered
# check if submitted before
# On call, should we return final score or raise error
# On pairing, if results is none for late submission, refund without bonus

# CorrectWeight = 0.8 (to give more weight to the number of correct answers)
# AnsweredWeight = 0.2 (to give less weight to the number of questions attempted)
# CorrectScore = (TotalCorrect / TotalQuestions) * CorrectWeight
# AnsweredScore = (TotalAnswered / TotalQuestions) * AnsweredWeight
# FinalScore = CorrectScore + AnsweredScore
