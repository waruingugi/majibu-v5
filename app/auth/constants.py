from enum import Enum

OTP_MESSAGE = "Your Majibu OTP is {}. Do not share it with anyone"


class TokenGrantType(Enum):
    IMPLICIT = "implict"
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    PASSWORD = "password"
    REFRESH_TOKEN = "refresh_token"
