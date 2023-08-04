from app.core.celery_app import celery

celery.autodiscover_tasks(
    packages=[
        "app",
        "app.sessions",
    ]
)
