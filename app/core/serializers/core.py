from pydantic import BaseModel


class ClosestIndexToScoreSerializer(BaseModel):
    right_index: int | None = None
    left_index: int | None = None
