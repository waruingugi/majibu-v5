from celery import shared_task

from app.core.logger import logger


@shared_task
def first_celery_task():
    logger.info("This is how we log celery tasks!.....")
    print("Task has run")
