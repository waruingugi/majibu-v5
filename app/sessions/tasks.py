from celery.utils.log import get_task_logger
from celery import shared_task


logger = get_task_logger(__name__)


@shared_task
def first_celery_task():
    logger.info("This is how we log celery tasks!.....")
    print("Task has run")
