from pydantic import BaseModel


class LoginSerializer(BaseModel):
    phone: str
