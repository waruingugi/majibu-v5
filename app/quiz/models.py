from app.db.base_class import Base
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Text, ForeignKey


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
