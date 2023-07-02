from fastapi import Depends
from sqlalchemy.orm import Session, load_only
from typing import Optional, Sequence

from app.core.deps import (
    get_db,
    get_current_active_user,
)
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

    def __call__(self, *, result_id: str, user: Optional[User] = None) -> str | None:
        self.user = self.user if user is None else user

        result_obj = result_dao.get_not_none(
            self.db,
            id=result_id,
            user_id=self.user.id,
            load_options=[load_only(Results.session_id, Results.expires_at)],
        )

        self.session_obj = session_dao.get_not_none(self.db, id=result_obj.session_id)

    def get_questions(self) -> Sequence:
        questions_obj = question_dao.search(
            self.db, search_filter=QuestionFilter(id__in=self.session_obj.questions)
        )
        return questions_obj

    def get_choices(self) -> Sequence:
        choices_obj = choice_dao.search(
            self.db,
            search_filter=ChoiceFilter(question_id__in=self.session_obj.questions),
        )
        return choices_obj


# If time expired, raise error for post
# Query sessions model for session id
# Query questions model for questions in list
# Query choices model for choices in list
# Sequence: {question_text: [choice, choice]} use map
# Create empty dict
# Loop through questions_obj
# Loop throuch choices_obj
# If question id same in both
# Append to dictionary
