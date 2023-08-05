from datetime import datetime, timedelta
import bisect
import heapq

from app.db.session import SessionLocal
from app.quiz.daos.quiz import result_dao
from app.quiz.serializers.quiz import ResultNodeSerializer
from app.core.serializers.core import ClosestNodeSerializer
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
                    self.ordered_scores_list, (result_in.score,)
                )

                self.ordered_scores_list.insert(index, (result_in.score, result_node))
                heapq.heappush(self.results_queue, result_node)

    def find_closest_node(self, score) -> ClosestNodeSerializer:
        """Find the closest nodes to a given score.
        Note: The elf.ordered_scores_list is never an empty list because the score being
        searched for, needs to exist inside the list too
        """
        # Put two recursive functions inside so that we don't have to pass score as an argument again
        def get_closest_index_to_the_right(index):
            """Recursion to find closest node to the right"""
            if (
                index + 1 == len(self.ordered_scores_list)
                or self.ordered_scores_list[index][0] != score
            ):
                return index
            return get_closest_index_to_the_right(index + 1)

        def get_closest_index_to_the_left(index):
            """Recursion to find closest node to the left"""
            if index - 1 == 0 or self.ordered_scores_list[index - 1][0] != score:
                return index - 1
            return get_closest_index_to_the_left(index - 1)

        # Use bisect_left & bisect_right to find the optimal insertion points
        left_index = bisect.bisect_left(self.ordered_scores_list, (score,))
        right_index = bisect.bisect_right(self.ordered_scores_list, (score,))

        if left_index == 0:
            """If the score index is at the beginning of the list,
            Then the closest node is always to the right."""
            closest_right_index = get_closest_index_to_the_right(left_index)
            return ClosestNodeSerializer(
                right_node=self.ordered_scores_list[closest_right_index]
            )

        elif right_index == len(self.ordered_scores_list):
            """If the index of the score is at the end of the list,
            Then the closest node is always to the left."""
            closest_left_index = get_closest_index_to_the_left(left_index)
            return ClosestNodeSerializer(
                left_node=self.ordered_scores_list[closest_left_index]
            )

        else:
            """If the index of the score is somewhere in the middle,
            then find closest nodes both to the left and right."""
            closest_right_index = get_closest_index_to_the_right(right_index)
            closest_left_index = get_closest_index_to_the_left(left_index)

            return ClosestNodeSerializer(
                right_node=self.ordered_scores_list[closest_right_index],
                left_node=self.ordered_scores_list[closest_left_index],
            )

    def calculate_mean_pairwise_difference(self):
        """Calculate the mean difference between consecutive scores"""
        if len(self.ordered_scores_list) > 1:
            differences = [
                abs(self.ordered_scores_list[i][0] - self.ordered_scores_list[i + 1][0])
                for i in range(len(self.ordered_scores_list) - 1)
            ]

            # Calculate the mean of the pair-wise differences
            mean_pair_wise_difference = sum(differences) / len(differences)
            return mean_pair_wise_difference

        return None


# Right, left
# if right == left (distance): use winloss ratio
# if right <= left or left >= right pair and EWMA
# if right only and not equal self and EWMA pair
# If left only and not equal to self and EWMA pair
# if right only and not EWMA refund
# if left only and not EWMA refund

# Create table, user_id, no_of_wins, no_of_losses, total_games
# Create table, total_users, EWMA, avg_pair_wise_diff, threshold
# Mean pairwise difference if less than 2
# Mean pairwise difference if 1 or 0
