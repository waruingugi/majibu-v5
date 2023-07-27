from app.core.celery_app import celery

from app.core.logger import logger


@celery.task(name=__name__ + ".first_celery_task")
def first_celery_task():
    logger.info("This is how we log celery tasks!.....")
    print("Task has run")
