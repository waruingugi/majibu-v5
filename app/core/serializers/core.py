from pydantic import BaseModel


class ClosestNodeSerializer(BaseModel):
    right_node: tuple | None = None
    left_node: tuple | None = None
