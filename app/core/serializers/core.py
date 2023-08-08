from pydantic import BaseModel


class ClosestNodeSerializer(BaseModel):
    right_node: tuple | None = None
    left_node: tuple | None = None


class PairPartnersSerializer(BaseModel):
    party_a: tuple | None = None
    party_b: tuple | None = None
