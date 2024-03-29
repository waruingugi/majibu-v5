from pydantic import BaseModel
from datetime import datetime


class ResultNode:
    def __init__(
        self,
        *,
        id: str,
        user_id: str,
        category: str,
        session_id: str,
        score: float,
        expires_at: datetime,
        is_active: bool
    ) -> None:
        """Represent each result model instance as a node"""
        self.id = id
        self.category = category
        self.user_id = user_id
        self.session_id = session_id
        self.score = score
        self.expires_at = expires_at
        self.is_active = is_active

    def __lt__(self, other_node) -> bool:
        """Heapq module uses this method to order nodes based on their expiry time.
        In simple terms, it uses this method when building a FIFO queue"""
        return self.expires_at < other_node.expires_at


class ClosestNodeSerializer(BaseModel):
    right_node: ResultNode | None = None
    left_node: ResultNode | None = None

    class Config:
        arbitrary_types_allowed = True


class PairPartnersSerializer(BaseModel):
    party_a: ResultNode
    party_b: ResultNode

    class Config:
        arbitrary_types_allowed = True
