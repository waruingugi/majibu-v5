import logging

from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed
from app.db.session import SessionLocal
from sqlalchemy import text

from app.core.config import redis as redis_server
import redis

from app.core.raw_logger import logger

max_tries = 60 * 5  # 5 minutes
redis_server_max_tries = 3
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init() -> None:
    try:
        db = SessionLocal()
        # Try to create session to check if DB is awake
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(e)
        raise e


def redis_is_running() -> None:
    try:
        redis_server.ping()
    except redis.ConnectionError as e:
        logger.error(e)
        raise e


def main() -> None:
    logger.info("Initailizing service")
    init()
    logger.info("Service finished initializing")
    logger.info("Checking redis-server is up")
    redis_is_running()
    logger.info("Redis-server is running")


if __name__ == "__main__":
    main()
