from datetime import datetime, timedelta
import bisect
import heapq

from app.db.session import SessionLocal
from app.quiz.daos.quiz import result_dao
from app.quiz.serializers.quiz import ResultNodeSerializer
from app.core.serializers.core import (
    ResultNode,
    ClosestNodeSerializer,
    PairPartnersSerializer,
)
from app.sessions.daos.session import pool_session_stats_dao
from app.core.config import settings
from app.core.logger import logger


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
                result_node = ResultNode(**result_in.dict())

                # Insert the node into the sorted list based on the score
                index = bisect.bisect_right(
                    self.ordered_scores_list, (result_in.score,)
                )

                self.ordered_scores_list.insert(index, (result_in.score, result_node))
                heapq.heappush(self.results_queue, result_node)

    def get_closest_nodes(self, node: ResultNode) -> ClosestNodeSerializer:
        """Find the closest nodes to a given score.
        Note: The elf.ordered_scores_list is never an empty list because the score being
        searched for, needs to exist inside the list too
        """

        def closest_node(index) -> ResultNode | None:
            """Return Node or None if there is no node"""
            return self.ordered_scores_list[index][1] if index else None

        # Put two recursive functions inside so that we don't have to pass score as an argument again
        def get_closest_index_to_the_right(index):
            """Recursion to find closest node to the right"""
            if (
                (self.ordered_scores_list[index][0] != score)  # If greater than score
                or (
                    index + 1 == len(self.ordered_scores_list)
                )  # Or node is the last elem in list
            ) and (  # And the session_id is the same...
                self.ordered_scores_list[index][1].session_id == session_id
            ):  # The a valid pair partner exists
                return index

            if index + 1 == len(self.ordered_scores_list):
                return None

            return get_closest_index_to_the_right(index + 1)

        def get_closest_index_to_the_left(index):
            """Recursion to find closest node to the left"""
            if (
                (self.ordered_scores_list[index - 1][0] != score)  # If less than score
                or (index - 1 == 0)  # Or node is the first element in list
            ) and (  # And the session_id is the same...
                self.ordered_scores_list[index - 1][1].session_id == session_id
            ):  # The a valid pair partner exists
                return index - 1

            if index - 1 == 0:
                return None

            return get_closest_index_to_the_left(index - 1)

        score = node.score
        session_id = node.session_id

        # Use bisect_left & bisect_right to find the optimal insertion points
        left_index = bisect.bisect_left(self.ordered_scores_list, (score,))
        right_index = bisect.bisect_right(self.ordered_scores_list, (score,))

        if left_index == 0:
            """If the score index is at the beginning of the list,
            Then the closest node is always to the right."""
            closest_right_index = get_closest_index_to_the_right(left_index)
            closest_right_node = closest_node(closest_right_index)
            return ClosestNodeSerializer(right_node=closest_right_node)

        elif right_index == len(self.ordered_scores_list):
            """If the index of the score is at the end of the list,
            Then the closest node is always to the left."""
            closest_left_index = get_closest_index_to_the_left(left_index)
            closest_left_node = closest_node(closest_left_index)

            return ClosestNodeSerializer(left_node=closest_left_node)

        else:
            """If the index of the score is somewhere in the middle,
            then find closest nodes both to the left and right."""
            closest_right_index = get_closest_index_to_the_right(right_index)
            closest_right_node = closest_node(closest_right_index)

            closest_left_index = get_closest_index_to_the_left(left_index)
            closest_left_node = closest_node(closest_left_index)

            return ClosestNodeSerializer(
                right_node=closest_right_node,
                left_node=closest_left_node,
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

    def calculate_average_score(self) -> float | None:
        """Calculate average score of the pool"""
        if not self.ordered_scores_list:
            return None  # Return None for an empty list

        total_score = sum(score for score, _ in self.ordered_scores_list)
        average_score = total_score / len(self.ordered_scores_list)
        return average_score

    def calculate_exp_weighted_moving_average(self) -> float:
        """Calculate the exponentially moving average"""
        avg_score = self.calculate_average_score() or 0

        with SessionLocal() as db:
            pool_session_stats = pool_session_stats_dao.search(
                db, {"order_by": ["-created_at"]}
            )
            if pool_session_stats:
                previous_session_stat = pool_session_stats[0]

                ewma = (settings.EWMA_MIXING_PARAMETER * avg_score) + (
                    1 - settings.EWMA_MIXING_PARAMETER
                ) * previous_session_stat.exp_weighted_moving_average
                return ewma

        return avg_score

    def create_duo_session(self):
        first_node = self.results_queue[0]

        time_to_expiry = datetime.now() - first_node.expires_at

        if time_to_expiry.seconds <= settings.RESULT_EXPIRES_AT_BUFFER_TIME:
            for node in self.results_queue:
                closest_nodes = self.get_closest_nodes(node)
                pair_partners = PairPartnersSerializer(party_a=node)

                right_node = closest_nodes.right_node
                right_node_dist = (
                    abs(node.score - right_node.score) if right_node else float("inf")
                )

                left_node = closest_nodes.left_node
                left_node_dist = (
                    abs(node.score - left_node.score) if left_node else float("inf")
                )

                # ------
                if (
                    left_node_dist == right_node_dist
                    and left_node is not None
                    and right_node is not None
                ):
                    pass

                elif left_node_dist < right_node_dist:
                    pair_partners.party_b = left_node

                elif right_node_dist < left_node_dist:
                    pair_partners.party_b = right_node

                else:
                    # set no partner, which means refund
                    pass

                #     # use win-loss ration and not inf for both
                # if left_node_distance < right_node_distance:
                #     # attempt pair(with ewma) for both nodes, preferred partner
                # if right_node_distance > left_node_distance:
                #     # attempt pair with right node and within ewma
                # else:
                #     # refund


# Right, left
# if right == left (distance): use winloss ratio
# if right <= left or left >= right pair and EWMA
# if right only and not equal self and EWMA pair
# If left only and not equal to self and EWMA pair
# if right only and not EWMA refund
# if left only and not EWMA refund

# Set win-loss ratio in Nodes
# If win-loss ration is same, choose random
# calculate ewma
# if queue > 1, save ewma to model
# Start pairing
# Refund if user did not attempt questions

# if distance same, choose any random
# else choose closests
# else if none refund

# On pairing
# if party_a has highest score and both parties not none,
# create duo session with values
# create transaction instance
# send message to boths users background func

# if partb has highest score and both parties not none
# do the same
# if part_a results none(answered no questsion) pure refund(move to top)
# transaction func different
# if part_a only and no partner full refund
# flood with logs
# else full refund
# At each if stage add to pop list
# if party_a only and no result pure refund
# elif if party-a only, full refund
# if pary_a and party_b - get winner at the top
# if get winner none refund party_a
# if get winner funct to run transactions, message , create instance
# pop both func using list
# remove win ratio from node, add to func
# Create pairpartner func
# --------------------------------------
# set ewma
# for node in results
# if time almost expiry and is active
# if result is none, partially refund user update stats
# Get closest node
# create pair partner functions, returns party_a or both parties
# get winners func, run ewma, results none: if both parties
# if response not none, add part_b to pop list
# remove nodes from queues, set false
# if winner, reward_winner, update stats
# else fully_refund user, update stats
