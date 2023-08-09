import logging
import sys
from functools import lru_cache
from typing import cast
import progressbar


progressbar.streams.wrap_stderr()
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
    format="[%(asctime)s] %(levelname)s - %(message)s",
)
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)


@lru_cache
def instantiate_logger() -> logging.Logger:
    logger_ = logging.getLogger(__name__)

    return logger_


logger = cast(logging.Logger, instantiate_logger())
