from celery import Celery
from app.core.config import settings
from celery.schedules import crontab


celery = Celery(
    __name__,
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_RESULT_BACKEND,
    timezone="Africa/Nairobi",
)


scheduled_tasks = {
    "update_business_partner_locations": {
        "task": "app.sessions.tasks.first_celery_task",
        "schedule": crontab(minute="*/1"),
        "options": {"queue": settings.CELERY_SCHEDULER_QUEUE},
    },
}

celery.conf.update(
    {"beat_schedule": scheduled_tasks, "redbeat_redis_url": settings.CELERY_BROKER}
)
