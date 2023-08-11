from app.db.base_class import Base
from app.core.config import settings

from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import String, Text, ForeignKey, Float, Integer
from typing import List


class UserSessionStats(Base):
    """User Session Stats model"""

    user_id = mapped_column(String, ForeignKey("user.id", ondelete="CASCADE"))
    total_wins = mapped_column(Integer, default=0)
    total_losses = mapped_column(Integer, default=0)
    sessions_played = mapped_column(Integer, default=0)

    @hybrid_property
    def win_ratio(self) -> float:
        if self.sessions_played == 0:  # Avoids Zero DivisionError
            return self.sessions_played
        return self.total_wins / self.sessions_played


class PoolSessionStats(Base):
    """Pool Session Statistics model"""

    total_players = mapped_column(Integer, nullable=True, default=0)
    mean_pairwise_difference = mapped_column(
        Float, nullable=True, comment="Mean pairwise difference of the pool"
    )
    threshold = mapped_column(
        Float,
        nullable=True,
        comment="The max. percentage of people who will be paired from the pool",
    )
    average_score = mapped_column(
        Float, nullable=True, comment="The average of scores in the pool"
    )
    pairing_range = mapped_column(
        Float,
        nullable=True,
        comment=(
            "A percentage of the EWMA. "
            "Two results(or Result Nodes) are paired if their score distances is within 0 - pairing_range."
        ),
    )
    exp_weighted_moving_average = mapped_column(
        Float,
        nullable=True,
        comment="The exponential moving average of pairwise diff. of the pool",
    )


class Sessions(Base):
    """Session model"""

    category = mapped_column(String, nullable=False)
    _questions = mapped_column("questions", Text())

    @hybrid_property
    def questions(self) -> List[str]:
        return self._questions.replace(" ", "").split(",")


class DuoSession(Base):
    """DuoSession model"""

    party_a = mapped_column(String, nullable=False)
    party_b = mapped_column(String, nullable=True)
    session_id = mapped_column(
        String, ForeignKey("sessions.id"), nullable=True, default=None
    )
    amount = mapped_column(
        Float(asdecimal=True, decimal_return_scale=settings.MONETARY_DECIMAL_PLACES),
        nullable=True,
        comment="This is the Amount that was transacted.",
    )
    status = mapped_column(String, nullable=True)
    winner_id = mapped_column(String, nullable=True)

    session = relationship("Sessions", backref="duo_session")
