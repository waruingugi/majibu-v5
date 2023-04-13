from pydantic import BaseModel
from enum import Enum
from app.db.serializer import InDBBaseSerializer


class TokenGrantType(Enum):
    IMPLICIT = "implict"
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    PASSWORD = "password"
    REFRESH_TOKEN = "refresh_token"


class TokenBaseSerializer(BaseModel):
    access_token: str
    user_id: str


class TokenReadSerializer(BaseModel):
    ...


class TokenCreateSerializer(BaseModel):
    ...


class TokenInDBSerializer(TokenBaseSerializer, InDBBaseSerializer):
    ...
