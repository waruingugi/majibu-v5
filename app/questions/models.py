from app.db.base_class import Base
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Text


class Questions(Base):
    category = mapped_column(String, nullable=False)
    question_text = mapped_column(Text, nullable=False)
