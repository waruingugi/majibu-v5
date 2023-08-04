from app.core.celery_app import celery

from app.core.logger import logger
from fastapi import Depends
from app.core.deps import business_is_open
from typing import Callable


@celery.task(name=__name__ + ".first_celery_task")
def first_celery_task(
    business_is_open: Callable = Depends(business_is_open),
):
    logger.info("This is how we log celery tasks!.....")
    print(f"Business is open: {business_is_open}")
