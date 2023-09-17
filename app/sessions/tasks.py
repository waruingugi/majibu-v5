from app.core.utils import PairUsers
from app.core.celery_app import celery
from app.core.logger import logger


# @celery.task(name=__name__ + ".first_celery_task")
# def first_celery_task():
#     pass


@celery.task(name=__name__ + ".pair_users_task", max_retries=0, acks_late=True)
def pair_users_task():
    """Periodically run the task of pairing users"""
    logger.info("Initiating pair users celery task")
    pair_users = PairUsers()
    pair_users.match_players()
