from datetime import datetime, timedelta
import bisect
import heapq

from app.db.session import SessionLocal
from app.quiz.daos.quiz import result_dao
from app.quiz.serializers.quiz import ResultNodeSerializer
from app.core.config import settings
from app.core.logger import logger


class Node:
    def __init__(self, *, user_id, session_id, score, expires_at, is_active) -> None:
        """Represent each result model instance as a node"""
        self.user_id = user_id
        self.session_id = session_id
        self.score = score
        self.expires_at = expires_at
        self.is_active = is_active

    def __lt__(self, other_node) -> bool:
        """Heapq module uses this method to order nodes based on their expiry time.
        In simple terms, it uses this method when building a FIFO queue"""
        return self.expires_at < other_node.expires_at


class PairUsers:
    def __init__(self) -> None:
        logger.info("Initializing PairUsers class...")
        self.ordered_scores_list = []
        self.results_queue = []

        self.create_nodes()

    def create_nodes(self) -> None:
        """Create Node instances for results that need to be paired"""
        logger.info("Creating nodes...")
        x_seconds_ago = datetime.now() - timedelta(
            seconds=settings.LOAD_SESSION_INTO_QUEUE_AFTER_SECONDS
        )

        with SessionLocal() as db:
            available_results = result_dao.search(
                db,
                {
                    "order_by": ["-created_at"],
                    "is_active": True,
                    "created_at__lt": x_seconds_ago,
                },
            )

            for result in available_results:
                logger.info(f"Create a node for result: {result.id}")
                result_in = ResultNodeSerializer(**result.__dict__)

                result_node = Node(**result_in.dict())
                # Insert the node into the sorted list based on the score
                index = bisect.bisect_right(
                    self.ordered_scores_list, (result_in.score, None)
                )

                self.ordered_scores_list.insert(index, (result_in.score, result_node))
                heapq.heappush(self.results_queue, result_node)
