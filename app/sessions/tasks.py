from app.core.celery_app import celery_app


@celery_app.task
def first_celery_task():
    print("Hurray, first task recognized!")
