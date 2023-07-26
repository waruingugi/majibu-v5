from app.core.celery_app import celery_app

celery_app.autodiscover_tasks(
    packages=[
        "app",
        "app.sessions",
    ]
)
