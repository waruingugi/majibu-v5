from pydantic import BaseModel
from datetime import datetime
from app.db.serializer import InDBBaseSerializer
from app.auth.constants import TokenGrantType


class TokenBaseSerializer(BaseModel):
    access_token: str
    user_id: str


class TokenReadSerializer(BaseModel):
    ...


class TokenCreateSerializer(TokenBaseSerializer):
    token_type: TokenGrantType
    access_token_eat: datetime
    is_active: bool = True


class TokenInDBSerializer(TokenBaseSerializer, InDBBaseSerializer):
    ...
