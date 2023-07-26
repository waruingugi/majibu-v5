from celery import Celery
from app.core.config import settings


celery = Celery(
    __name__,
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_RESULT_BACKEND,
    timezone="Africa/Nairobi",
)
