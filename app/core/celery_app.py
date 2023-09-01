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
    # Run a period task that pairs users, this is the heart of the system
    "pair_users_in_pool": {
        "task": "app.sessions.tasks.pair_users_task",
        "schedule": crontab(minute="*/3"),
        "options": {"queue": settings.CELERY_SCHEDULER_QUEUE},
    },
}

celery.conf.update(
    {"beat_schedule": scheduled_tasks, "redbeat_redis_url": settings.CELERY_BROKER}
)
