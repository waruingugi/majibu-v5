from app.db.base_class import Base
from sqlalchemy.orm import mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import String, Text
from typing import List


class Sessions(Base):
    category = mapped_column(String, nullable=False)
    _questions = mapped_column("questions", Text())

    @hybrid_property
    def questions(self) -> List[int]:
        return self._questions.replace(" ", "").split(",")
