from app.db.base_class import Base
from app.core.config import settings

from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import String, Text, ForeignKey, Float, Boolean
from typing import List


class Sessions(Base):
    category = mapped_column(String, nullable=False)
    _questions = mapped_column("questions", Text())

    @hybrid_property
    def questions(self) -> List[int]:
        return self._questions.replace(" ", "").split(",")


class DuoSession(Base):
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
    status = mapped_column(Boolean, default=True)
    winner_id = mapped_column(String, nullable=True)

    session = relationship("Sessions", backref="duo_session")
