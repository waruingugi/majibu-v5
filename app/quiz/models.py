from app.db.base_class import Base
from app.core.config import settings

from sqlalchemy import Float, text, DateTime, Boolean
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Text, ForeignKey, Integer


class Questions(Base):
    category = mapped_column(String, nullable=False)
    question_text = mapped_column(Text, nullable=False)


class Choices(Base):
    question_id = mapped_column(String, ForeignKey("questions.id", ondelete="CASCADE"))
    choice_text = mapped_column(Text, nullable=False)


class Answers(Base):
    question_id = mapped_column(
        String, ForeignKey("questions.id", ondelete="CASCADE"), unique=True
    )
    choice_id = mapped_column(String, ForeignKey("choices.id", ondelete="CASCADE"))


class Results(Base):
    user_id = mapped_column(String, ForeignKey("user.id", ondelete="CASCADE"))
    session_id = mapped_column(String, ForeignKey("sessions.id", ondelete="CASCADE"))
    percentage = mapped_column(
        Float(
            asdecimal=True, decimal_return_scale=settings.SESSION_RESULT_DECIMAL_PLACES
        ),
        nullable=True,
        server_default=text("0.0"),
        default=0.0,
        comment=("The total based on how they answered questions"),
    )
    total_answered = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment=("Number of total answered questions"),
    )
    speed = mapped_column(
        Float(
            asdecimal=True, decimal_return_scale=settings.SESSION_RESULT_DECIMAL_PLACES
        ),
        nullable=True,
        server_default=text("0.0"),
        default=0.0,
        comment=("The total of how fast the user is during the session"),
    )
    time_taken = mapped_column(
        Float(
            asdecimal=True, decimal_return_scale=settings.SESSION_RESULT_DECIMAL_PLACES
        ),
        nullable=True,
        server_default=text("0.0"),
        default=0.0,
        comment=(
            "Time taken to play the session(that is, to answer questions) in milliseconds"
        ),
    )
    score = mapped_column(
        Float(
            asdecimal=True, decimal_return_scale=settings.SESSION_RESULT_DECIMAL_PLACES
        ),
        nullable=True,
        server_default=text("0.0"),
        default=0.0,
        comment=(
            "The total marks based on all weights, formula and other criteria. "
            "This what is shown to the user"
        ),
    )
    expires_at = mapped_column(
        DateTime,
        nullable=False,
        comment=("When the session expires and is no longer available to the user"),
    )
    is_active = mapped_column(
        Boolean,
        default=True,
        comment=("If these results can be used to create pair with another user"),
    )
