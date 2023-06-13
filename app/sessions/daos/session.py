from sqlalchemy.orm import Session

from app.db.dao import CRUDDao
from app.core.helpers import convert_list_to_string
from app.exceptions.custom import QuestionExistsInASession
from app.sessions.models import Sessions
from app.sessions.serializers.session import (
    SessionCreateSerializer,
    SessionUpdateSerializer,
)


class SessionDao(CRUDDao[Sessions, SessionCreateSerializer, SessionUpdateSerializer]):
    def session_has_unique_questions(self, db: Session, values: dict) -> None:
        sessions = self.get_all(db)
        existing_questions = []

        for session in sessions:
            existing_questions.extend(session.questions)

        for question in values["questions"]:
            if question in existing_questions:
                raise QuestionExistsInASession(
                    f"The question id {question} exists in another session"
                )

    def on_pre_create(
        self, db: Session, id: str, values: dict, orig_values: dict
    ) -> None:
        self.session_has_unique_questions(db, orig_values)

        values["questions"] = convert_list_to_string(orig_values.get("questions", []))

    def on_pre_update(
        self, db: Session, db_obj: Sessions, values: dict, orig_values: dict
    ) -> None:
        values["questions"] = convert_list_to_string(orig_values.get("questions", []))


session_dao = SessionDao(Sessions)
