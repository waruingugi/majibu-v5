from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from app.db.dao import CRUDDao
from app.core.config import settings
from app.core.helpers import convert_list_to_string, generate_transaction_code

from app.users.daos.user import user_dao
from app.accounts.daos.account import transaction_dao
from app.accounts.constants import (
    TransactionTypes,
    TransactionCashFlow,
    TransactionServices,
    SESSION_LOSS_MESSAGE,
    SESSION_REFUND_MESSAGE,
    SESSION_WIN_DESCRIPION,
    REFUND_SESSION_DESCRIPTION,
    SESSION_PARTIAL_REFUND_MESSAGE,
    PARTIALLY_REFUND_SESSION_DESCRIPTION,
)
from app.accounts.serializers.account import TransactionCreateSerializer

from app.accounts.constants import SESSION_WIN_MESSAGE
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

from app.notifications.daos.notifications import notifications_dao
from app.notifications.constants import NotificationChannels, NotificationTypes
from app.notifications.serializers.notifications import CreateNotificationSerializer


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

    def on_post_create(
        self,
        db: Session,
        db_obj: DuoSession,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Update user wallets and send notifications"""

        def send_message(phone: str, message: str) -> None:
            """Send message to DuoSession players"""
            channel = NotificationChannels.SMS.value
            type = NotificationTypes.SESSION.value

            background_tasks.add_task(
                notifications_dao.send_notification,
                db,
                obj_in=CreateNotificationSerializer(
                    channel=channel,
                    phone=phone,
                    message=message,
                    type=type,
                ),
            )

        """Updates the winner's wallet to reflect the new amount"""
        if db_obj.status == DuoSessionStatuses.PAIRED:
            winner = user_dao.get_not_none(db, id=db_obj.winner_id)
            description = SESSION_WIN_DESCRIPION.format(winner.phone, db_obj.session_id)

            amount_won = settings.SESSION_WIN_RATIO * float(db_obj.amount)
            winner_message = SESSION_WIN_MESSAGE.format(amount_won, db_obj.category)

            transaction_dao.create(
                db,
                obj_in=TransactionCreateSerializer(
                    account=winner.phone,
                    external_transaction_id=generate_transaction_code(),
                    cash_flow=TransactionCashFlow.INWARD.value,
                    type=TransactionTypes.DEPOSIT.value,
                    service=TransactionServices.SESSION.value,
                    description=description,
                    amount=amount_won,
                ),
            )

            # Send message to the winner
            send_message(winner.phone, winner_message)

            # Get the opponent id
            opponent_id = (
                db_obj.party_a if winner.id != db_obj.party_a else db_obj.party_b
            )
            opponent = user_dao.get_not_none(db, id=opponent_id)
            opponent_message = SESSION_LOSS_MESSAGE.format(db_obj.category)

            # Send message to the opponent
            send_message(opponent.phone, opponent_message)

        """Update party_a's wallet to reflect the refund"""
        if db_obj.status == DuoSessionStatuses.REFUNDED:
            user = user_dao.get_not_none(db, id=db_obj.party_a)
            description = REFUND_SESSION_DESCRIPTION.format(
                user.phone, db_obj.session_id
            )
            refund_amount = settings.SESSION_REFUND_RATIO * float(db_obj.amount)
            refund_message = SESSION_REFUND_MESSAGE.format(
                refund_amount, db_obj.category
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
                    amount=refund_amount,
                ),
            )

            # Send message to party_a on refund
            send_message(user.phone, refund_message)

        """Update party_a's wallet to reflect the partial refund"""
        if db_obj.status == DuoSessionStatuses.PARTIALLY_REFUNDED:
            user = user_dao.get_not_none(db, id=db_obj.party_a)
            description = PARTIALLY_REFUND_SESSION_DESCRIPTION.format(
                user.phone, db_obj.session_id
            )

            partial_refund_amount = settings.SESSION_PARTIAL_REFUND_RATIO * float(
                db_obj.amount
            )
            partial_refund_message = SESSION_PARTIAL_REFUND_MESSAGE.format(
                partial_refund_amount, db_obj.category
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

            # Send message to party_a on partial refund
            send_message(user.phone, partial_refund_message)


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
