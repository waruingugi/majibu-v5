from sqlalchemy.orm import Session

from app.db.dao import CRUDDao
from app.core.config import settings
from app.core.helpers import convert_list_to_string, generate_transaction_code

from app.users.daos.user import user_dao
from app.accounts.daos.account import transaction_dao
from app.accounts.constants import (
    TransactionTypes,
    TransactionCashFlow,
    TransactionServices,
    SESSION_WIN_DESCRIPION,
    REFUND_SESSION_DESCRIPTION,
    PARTIALLY_REFUND_SESSION_DESCRIPTION,
)
from app.accounts.serializers.account import TransactionCreateSerializer

from app.exceptions.custom import DuoSessionFailedOnCreate
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
from app.sessions.constants import DuoSessionStatuses


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
        """Automatically assign value to the _statisitics value"""
        values["_statistics"] = orig_values["statistics"]


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
    def on_pre_create(
        self, db: Session, id: str, values: dict, orig_values: dict
    ) -> None:
        """Check these constraints before creating a DuoSession instance in the model."""
        # Constraint 1: Parties can not play a session_id twice
        """Assert that none of the parties have played a DuoSession with the same session_id before."""
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
            dup_session = sessions_played.pop()  # Duplicate session
            user_id = (
                dup_session.party_a if dup_session.party_a else dup_session.party_a
            )
            raise DuoSessionFailedOnCreate(
                f"The user_id: {user_id} has this played the Duo Session id: {dup_session.id} before."
            )

        # Constraint 2: party_a and party_b can never be the same in a DuoSession instance
        if "party_a" in orig_values and "party_b" in orig_values:
            if orig_values["party_a"] == orig_values["party_b"]:
                raise DuoSessionFailedOnCreate(
                    f"Party A & Party B can not be the same for a DuoSession. "
                    f"Please update {orig_values['party_b']}"
                )

        # Constraint 3: party_b should not exist for PARTIAL_REFUNDS or REFUNDS.
        # Only party_a is to be refunded
        if "party_b" in orig_values and (
            orig_values["status"] == DuoSessionStatuses.PARTIALLY_REFUNDED.value
            or orig_values["status"] == DuoSessionStatuses.REFUNDED.value
        ):
            raise DuoSessionFailedOnCreate(
                f"Party B should not exist for {orig_values['status']}. "
                f"Please remove {orig_values['party_b']}"
            )

    def on_post_create(self, db: Session, db_obj: DuoSession) -> None:
        """Update user wallets"""
        if db_obj.status == DuoSessionStatuses.PAIRED:
            # Updates the winner's wallet to reflect the new amount
            user = user_dao.get_not_none(db, id=db_obj.winner_id)
            description = SESSION_WIN_DESCRIPION.format(user.phone, db_obj.session_id)
            amount_won = settings.SESSION_WIN_RATIO * float(db_obj.amount)

            transaction_dao.create(
                db,
                obj_in=TransactionCreateSerializer(
                    account=user.phone,
                    external_transaction_id=generate_transaction_code(),
                    cash_flow=TransactionCashFlow.INWARD.value,
                    type=TransactionTypes.DEPOSIT.value,
                    service=TransactionServices.SESSION.value,
                    description=description,
                    amount=amount_won,
                ),
            )

        if db_obj.status == DuoSessionStatuses.REFUNDED:
            # Update party_a's wallet to reflect the refund
            user = user_dao.get_not_none(db, id=db_obj.party_a)
            description = REFUND_SESSION_DESCRIPTION.format(
                user.phone, db_obj.session_id
            )
            refund_amount = settings.SESSION_REFUND_RATIO * float(db_obj.amount)

            transaction_dao.create(
                db,
                obj_in=TransactionCreateSerializer(
                    account=user.phone,
                    external_transaction_id=generate_transaction_code(),
                    cash_flow=TransactionCashFlow.INWARD.value,
                    type=TransactionTypes.REFUND.value,
                    service=TransactionServices.SESSION.value,
                    description=description,
                    amount=refund_amount,
                ),
            )

        if db_obj.status == DuoSessionStatuses.PARTIALLY_REFUNDED:
            # Update party_a's wallet to reflect the partial refund
            user = user_dao.get_not_none(db, id=db_obj.party_a)
            description = PARTIALLY_REFUND_SESSION_DESCRIPTION.format(
                user.phone, db_obj.session_id
            )
            partial_refund_amount = settings.SESSION_PARTIAL_REFUND_RATIO * float(
                db_obj.amount
            )

            transaction_dao.create(
                db,
                obj_in=TransactionCreateSerializer(
                    account=user.phone,
                    external_transaction_id=generate_transaction_code(),
                    cash_flow=TransactionCashFlow.INWARD.value,
                    type=TransactionTypes.REFUND.value,
                    service=TransactionServices.SESSION.value,
                    description=description,
                    amount=partial_refund_amount,
                ),
            )


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
