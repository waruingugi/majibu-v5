from sqlalchemy.orm import Session

from app.exceptions.custom import DuoSessionAlreadyExists
from app.db.dao import CRUDDao
from app.core.helpers import convert_list_to_string
from app.core.config import settings
from app.exceptions.custom import QuestionExistsInASession, FewQuestionsInSession
from app.sessions.models import (
    Sessions,
    DuoSession,
    UserSessionStats,
    PoolSessionStats,
)
from app.sessions.serializers.session import (
    SessionCreateSerializer,
    SessionUpdateSerializer,
    DuoSessionCreateSerializer,
    DuoSessionUpdateSerializer,
    UserSessionStatsCreateSerializer,
    UserSessionStatsUpdateSerializer,
    PoolSessionStatsCreateSerializer,
    PoolSessionStatsUpdateSerializer,
)
from app.sessions.filters import DuoSessionFilter


class PoolSessionStatsDao(
    CRUDDao[
        PoolSessionStats,
        PoolSessionStatsCreateSerializer,
        PoolSessionStatsUpdateSerializer,
    ]
):
    def on_pre_create(
        self, db: Session, id: str, values: dict, orig_values: dict
    ) -> None:
        """Automatically compute the pairing_range field and set it to the model"""
        values["pairing_range"] = (
            values["exp_weighted_moving_average"] * settings.PAIRING_THRESHOLD
        )


pool_session_stats_dao = PoolSessionStatsDao(PoolSessionStats)


class UserSessionStatsDao(
    CRUDDao[
        UserSessionStats,
        UserSessionStatsCreateSerializer,
        UserSessionStatsUpdateSerializer,
    ]
):
    def get_or_create(
        self,
        db: Session,
        obj_in: UserSessionStatsCreateSerializer,
    ) -> UserSessionStats:
        """Get or create a UserSessionStats"""
        user_session_stats_in = self.get(db, user_id=obj_in.user_id)
        if not user_session_stats_in:
            user_session_stats_data = UserSessionStatsCreateSerializer(**obj_in.dict())
            user_session_stats_in = self.create(db, obj_in=user_session_stats_data)

        return user_session_stats_in


user_session_stats_dao = UserSessionStatsDao(UserSessionStats)


class DuoSessionDao(
    CRUDDao[DuoSession, DuoSessionCreateSerializer, DuoSessionUpdateSerializer]
):
    # Updates on DuoSession are no longer supported
    # def on_pre_update(
    #     self, db: Session, db_obj: DuoSession, values: dict, orig_values: dict
    # ) -> None:
    #     """Run validation checks before updating DuoSession instance"""
    #     if db_obj.party_a == values["party_b"]:
    #         raise DuoSessionFailedOnUpdate(
    #             f"Can not pair user id{db_obj.party_a} to themselves"
    #         )
    def on_pre_create(
        self, db: Session, id: str, values: dict, orig_values: dict
    ) -> None:
        """Assert not on the parties have played a DuoSession with the same session_id before."""
        sessions_played = []

        # Search if party_a has played this DuoSession before
        if "party_a" in orig_values:
            party_a_sessions = self.search(
                db,
                search_filter=DuoSessionFilter(
                    search=orig_values["party_a"],  # type: ignore
                    session_id=orig_values["session_id"],
                ),
            )
            sessions_played.extend(party_a_sessions)

        # Search if party_b has played this DuoSession before
        if "party_b" in orig_values:
            party_b_sessions = self.search(
                db,
                search_filter=DuoSessionFilter(
                    search=orig_values["party_b"],  # type: ignore
                    session_id=orig_values["session_id"],
                ),
            )
            sessions_played.extend(party_b_sessions)

        """If any of the parties have played the session before, raise an exception"""
        if sessions_played:
            raise DuoSessionAlreadyExists(values["party_a"], orig_values["session_id"])


duo_session_dao = DuoSessionDao(DuoSession)


class SessionDao(CRUDDao[Sessions, SessionCreateSerializer, SessionUpdateSerializer]):
    def session_has_unique_questions(self, db: Session, values: dict) -> None:
        """A question should not exist twice in any session"""
        sessions = self.get_all(db)
        existing_questions = []

        for session in sessions:
            existing_questions.extend(session.questions)

        for question in values["questions"]:
            if question in existing_questions:
                raise QuestionExistsInASession(
                    f"The question id {question} exists in another session"
                )

    def session_has_enough_questions(self, value) -> None:
        """Test session has correct number of questions"""
        if len(value) != settings.QUESTIONS_IN_SESSION:
            raise FewQuestionsInSession()

    def on_pre_create(
        self, db: Session, id: str, values: dict, orig_values: dict
    ) -> None:
        """Run validations before create"""
        self.session_has_unique_questions(db, orig_values)

        self.session_has_enough_questions(orig_values["questions"])

        values["questions"] = convert_list_to_string(orig_values.get("questions", []))

    def on_pre_update(
        self, db: Session, db_obj: Sessions, values: dict, orig_values: dict
    ) -> None:
        values["questions"] = convert_list_to_string(orig_values.get("questions", []))


session_dao = SessionDao(Sessions)
