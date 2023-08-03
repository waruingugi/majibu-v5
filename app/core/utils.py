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

    def find_closest_nodes(self, target_score, ordered_scores):
        """Find the closest nodes to a given score"""

        def get_closest_node_to_the_right(index):
            """Recursion to find closest node to the right"""
            if (
                index + 1 == len(ordered_scores)
                or ordered_scores[index] != target_score
            ):
                return ordered_scores[index]
            return get_closest_node_to_the_right(index + 1)

        def get_closest_node_to_the_left(index):
            """Recursion to find closest node to the left"""
            if index - 1 == 0 or ordered_scores[index - 1] != target_score:
                return ordered_scores[index - 1]
            return get_closest_node_to_the_left(index - 1)

        # Use bisect_left & bisect_right to find the optimal insertion points
        left_index = bisect.bisect_left(ordered_scores, target_score)
        right_index = bisect.bisect_right(ordered_scores, target_score)

        if left_index == 0:
            """If the score index is at the beginning of the list,
            Then the closest node is always to the right."""
            closest_right = get_closest_node_to_the_right(left_index)
            return closest_right

        elif right_index == len(ordered_scores):
            """If the index of the score is at the end of the list,
            Then the closest node is always to the left."""
            closest_left = get_closest_node_to_the_left(left_index)
            return closest_left

        else:
            """If the index of the score is somewhere in the middle,
            then find closest nodes both to the left and right."""
            closest_right = get_closest_node_to_the_right(left_index)
            closest_left = get_closest_node_to_the_left(left_index)

            return closest_left, closest_right


# import bisect

# def find_closest_score(target_score, ordered_scores):
#     # Use bisect.bisect_left to find the left insertion point
#     left_index = bisect.bisect_left(ordered_scores, target_score)

#     # If the target score is at the beginning of the list, the closest score is the second element
#     if left_index == 0:
#         closest_right = ordered_scores[1]
#         return closest_right if closest_right != target_score else ordered_scores[2]

#     # If the target score is at the end of the list, the closest score is the second last element
#     if left_index == len(ordered_scores):
#         closest_left = ordered_scores[-2]
#         return closest_left if closest_left != target_score else ordered_scores[-3]

#     # The target score is somewhere in the middle of the list
#     closest_left = ordered_scores[left_index - 1]
#     closest_right = ordered_scores[left_index + 1]

#     # Check if target_score is the same as closest_left or closest_right
#     if closest_left == target_score:
#         return ordered_scores[left_index + 2]
#     if closest_right == target_score:
#         return ordered_scores[left_index - 2]

#     # Choose the closest score on either side of the target score
#     return closest_left if target_score - closest_left <= closest_right - target_score else closest_right

# # Example usage:
# ordered_scores = [72, 75, 78, 80, 80, 83, 86]
# target_score = 80

# closest_score = find_closest_score(target_score, ordered_scores)
# print("Closest score to", target_score, "is", closest_score)


# score is always in the list
# If score right and left are the same
# Use win-score ration
# Case where list is empty
# Case where only the one in list
# Case where only similar score or two  or more similar scores in list
# Case where other scores in list along with the one shared
