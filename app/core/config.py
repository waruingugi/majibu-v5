from functools import lru_cache
from pydantic import BaseSettings, PostgresDsn
from typing import cast
from redis import Redis


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

    SUPERUSER_FIRST_NAME: str
    SUPERUSER_LAST_NAME: str
    SUPERUSER_PHONE: str

    REDIS_HOST: str = "localhost"
    REDIS_PASSWORD: str | None
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

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
