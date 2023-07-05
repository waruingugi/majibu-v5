from functools import lru_cache
from pydantic import BaseSettings, PostgresDsn
from typing import cast
from redis import Redis
from fastapi.templating import Jinja2Templates

from os.path import dirname
import app


# Template configurations
project_dir = dirname(app.__file__)
templates = Jinja2Templates(directory=project_dir)

# Global filters
# Add comma to digits. Example: 1000 -> 1,000
templates.env.filters["commafy"] = lambda v: "{:,}".format(v)


# Settings
class Settings(BaseSettings):
    PROJECT_NAME: str = "Majibu"
    API_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRY_IN_SECONDS: int = 60 * 60 * 24
    REFRESH_TOKEN_EXPIRY_IN_SECONDS: int = 60 * 60 * 7

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str

    SQLALCHEMY_DATABASE_URI: PostgresDsn
    ASYNC_SQLALCHEMY_DATABASE_URI: PostgresDsn

    HOST_PINNACLE_SENDER_ID: str
    HOST_PINNACLE_PASSWORD: str
    HOST_PINNACLE_USER_ID: str
    HOST_PINNACLE_SMS_BASE_URL: str

    MOBI_TECH_API_KEY: str
    MOBI_TECH_SMS_BASE_URL: str
    MOBI_TECH_SENDER_NAME: str

    TOTP_EXPIRY_TIME: int = 300  # Time in seconds
    TOTP_LENGTH: int = 4

    DEFAULT_SMS_PROVIDER: str

    REDIS_HOST: str = "localhost"
    REDIS_PASSWORD: str | None
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    DEFAULT_COUNTRY_ISO2_CODE: str = "KE"

    SUPERUSER_PHONE: str

    SESSION_AMOUNT: int = 500
    SESSION_FEE: float = 45.0

    MPESA_B2C_CHARGE: int = 16
    MPESA_B2C_CONSUMER_KEY: str
    MPESA_B2C_SECRET: str
    MPESA_B2C_URL: str
    MPESA_B2C_PASSWORD: str
    MPESA_B2C_SHORT_CODE: str
    MPESA_B2C_INITIATOR_NAME: str
    MPESA_B2C_QUEUE_TIMEOUT_URL: str
    MPESA_B2C_RESULT_URL: str

    MPESA_BUSINESS_SHORT_CODE: str
    MPESA_PASS_KEY: str
    MPESA_CONSUMER_KEY: str
    MPESA_SECRET: str
    MPESA_DATETIME_FORMAT: str = "%Y%m%d%H%M%S"
    MPESA_CALLBACK_URL: str
    MPESA_TOKEN_URL: str = (
        "https://sandbox.safaricom.co.ke/oauth/v1/"
        "generate?grant_type=client_credentials"
    )
    MPESA_STKPUSH_URL: str = (
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    )
    MPESA_STKPUSH_QUERY_URL: str = (
        "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
    )

    MONETARY_DECIMAL_PLACES: int = 2  # Decimal places to use for all monetary values

    QUESTIONS_IN_SESSION: int = 5
    CHOICES_IN_QUESTION: int = 5
    SESSION_RESULT_DECIMAL_PLACES: int = 7  # High accuracy to pevent draws
    SESSION_DURATION: int = 15  # How long the session lasts

    MAINTENANCE_MODE: int = 0
    BUSINESS_OPENS_AT: str
    BUSINESS_CLOSES_AT: str

    WITHDRAWAL_BUFFER_PERIOD: int = 120  # Once every 2 minutes

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_app_settings() -> Settings:
    return Settings()  # type: ignore


# settings = Settings()
settings = cast(Settings, get_app_settings())


ASYNC_SQLALCHEMY_DATABASE_URI = PostgresDsn.build(
    scheme="postgresql+asyncpg",
    user=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.POSTGRES_SERVER,
    path=f"/{settings.POSTGRES_DB}",
    port=settings.POSTGRES_PORT,
)

SQLALCHEMY_DATABASE_URI = PostgresDsn.build(
    scheme="postgresql+psycopg2",
    user=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.POSTGRES_SERVER,
    path=f"/{settings.POSTGRES_DB}",
    port=settings.POSTGRES_PORT,
)


@lru_cache
def get_redis() -> Redis:
    return Redis(
        host=settings.REDIS_HOST or "localhost",
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        decode_responses=True,
    )


redis = cast(Redis, get_redis())
