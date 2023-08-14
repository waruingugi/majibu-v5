import bisect
import heapq
import random
from datetime import datetime, timedelta

from app.db.session import SessionLocal

from app.core.config import settings
from app.core.logger import logger
from app.core.serializers.core import (
    ResultNode,
    ClosestNodeSerializer,
    PairPartnersSerializer,
)

from app.quiz.daos.quiz import result_dao
from app.quiz.serializers.quiz import ResultNodeSerializer

from app.sessions.constants import DuoSessionStatuses
from app.sessions.daos.session import pool_session_stats_dao, duo_session_dao
from app.sessions.serializers.session import (
    PoolSessionStatsCreateSerializer,
    DuoSessionCreateSerializer,
)


class PairUsers:
    def __init__(self) -> None:
        logger.info("Initializing PairUsers class...")
        self.ordered_scores_list = []
        self.results_queue = []

        self.ewma = float("inf")
        self.pairing_range = float("inf")

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
        Note: The self.ordered_scores_list is never an empty list because the score being
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
        mean_pairwise_diff = self.calculate_mean_pairwise_difference() or 0

        with SessionLocal() as db:
            pool_session_stats = pool_session_stats_dao.search(
                db, {"order_by": ["-created_at"]}
            )

            if pool_session_stats:
                previous_session_stat = pool_session_stats[0]
                ewma = (settings.EWMA_MIXING_PARAMETER * mean_pairwise_diff) + (
                    1 - settings.EWMA_MIXING_PARAMETER
                ) * previous_session_stat.exp_weighted_moving_average

                return ewma

        return mean_pairwise_diff

    def set_pool_session_statistics(self) -> None:
        """Set statistics to the PoolSession model"""
        with SessionLocal() as db:
            average_score = self.calculate_average_score()
            mean_pair_wise_diff = self.calculate_mean_pairwise_difference()
            ewma = self.calculate_exp_weighted_moving_average()

            pool_session_stats_dao.create(
                db,
                obj_in=PoolSessionStatsCreateSerializer(
                    total_players=len(self.results_queue),
                    average_score=average_score,
                    mean_pairwise_difference=mean_pair_wise_diff,
                    exp_weighted_moving_average=ewma,
                ),
            )

    def get_pair_partner(
        self, target_node: ResultNode, closest_nodes_in: ClosestNodeSerializer
    ) -> ResultNode | None:
        """Receives No nodes, one or two nodes then returns the node closest to the target score"""
        right_node = closest_nodes_in.right_node
        left_node = closest_nodes_in.left_node

        closest_node = None  # If no node is found, return None
        sibling_nodes = [right_node, left_node]
        closest_score_diff = float("inf")
        same_score_nodes = []

        for node in sibling_nodes:
            # If node is None, assign score to infinity
            node_score = float("inf") if node is None else node.score
            score_diff = abs(target_node.score - node_score)

            if score_diff < closest_score_diff:
                closest_node = node
                closest_score_diff = score_diff
                same_score_nodes = [node]

            elif score_diff == closest_score_diff:
                same_score_nodes.append(node)

        if same_score_nodes:
            """If both nodes have same score, choose a random node and return it"""
            closest_node = random.choice(same_score_nodes)

        return closest_node

    def get_winner(self, pair_partners: PairPartnersSerializer) -> ResultNode | None:
        """Returns the winner between two nodes, else, it returns None"""
        party_a = pair_partners.party_a
        party_b = pair_partners.party_b
        winner = None

        score_diff = abs(party_a.score - party_b.score)

        # Check if both nodes are within pairing range
        if score_diff <= self.pairing_range:
            winner = party_a if party_a.score > party_b.score else party_b

        return winner

    def create_duo_session(
        self,
        *,
        party_a: ResultNode,
        party_b: ResultNode | None,
        winner: ResultNode | None,
        duo_session_status: DuoSessionStatuses,
    ) -> None:
        """Finally create a DuoSession so that the parties receive their funds"""
        duo_session_in = DuoSessionCreateSerializer(
            party_a=party_a.user_id,
            party_b=party_b.user_id if party_b else None,
            winner_id=winner.user_id if winner else None,
            session_id=party_a.session_id,
            status=duo_session_status.value,
        )
        with SessionLocal() as db:
            duo_session_dao.create(db, obj_in=duo_session_in)

    def remove_nodes_from_pool(self, nodes_to_remove: list) -> None:
        """Remove the node from both the queue and ordered list"""
        for score, node in self.ordered_scores_list:
            if node in nodes_to_remove:
                self.ordered_scores_list.remove((score, node))

        for node in self.results_queue:
            if node in nodes_to_remove:
                self.results_queue.remove(node)

        heapq.heapify(self.results_queue)

    def deactivate_results(self, result_nodes: list) -> None:
        """Deactives both the node and the Result model instance"""
        with SessionLocal() as db:
            for node in result_nodes:
                node.is_active = False
                result_obj = result_dao.get_not_none(db, id=node.id)
                result_dao.update(db, db_obj=result_obj, obj_in={"is_active": False})

    def match_players(self):
        """Loops through PoolSession to get players, find partners, or refund them"""
        self.ewma = self.calculate_exp_weighted_moving_average()
        self.pairing_range = self.ewma * settings.PAIRING_THRESHOLD

        # Save the current PoolSesssion stats to model
        self.set_pool_session_statistics()

        for node in self.results_queue:
            """If node is x seconds close to expiry, then it's eligible to be paired"""
            time_to_expiry = node.expires_at - timedelta(
                seconds=settings.RESULT_EXPIRES_AT_BUFFER_TIME
            )

            party_a = node
            nodes_to_remove = []
            winner, party_b = None, None
            duo_session_status = DuoSessionStatuses.REFUNDED

            if node.is_active and datetime.now() > time_to_expiry:
                if node.score == 0.0:
                    """The user played a session, but did not answer at least one question.
                    So we do a partial refund. To receive a full refund, attempt to answer atleast
                    one question"""
                    duo_session_status = DuoSessionStatuses.PARTIALLY_REFUNDED
                    nodes_to_remove = [party_a]

                else:
                    """
                    The user attempted atleast one question, so try to find a partner to pair with the user.
                    """
                    closest_nodes = self.get_closest_nodes(node)
                    party_b = self.get_pair_partner(node, closest_nodes)

                    if party_b is not None:
                        """If a pairing partner was found, get the winner between party_a and party_b"""
                        winner = self.get_winner(
                            PairPartnersSerializer(party_a=node, party_b=party_b)
                        )

                        """If there's no winner, then set the status us REFUNDED so that party_a is refunded
                        and party_b is returned to the pool."""
                        if winner is not None:  # A winner was found
                            duo_session_status = DuoSessionStatuses.PAIRED
                            nodes_to_remove = [party_a, party_b]
                        else:
                            duo_session_status = DuoSessionStatuses.REFUNDED
                            nodes_to_remove = [party_a]

                self.deactivate_results(nodes_to_remove)

                self.remove_nodes_from_pool(nodes_to_remove)

                self.create_duo_session(
                    party_a=party_a,
                    party_b=party_b,
                    winner=winner,
                    duo_session_status=duo_session_status,
                )


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
# Get mean pairwise diff or none, save to model automatically
# Search recent ewma based on time,
# If none, use current mean_pairwise diff
# if results > 1
# set ewma
# ----
# Duo sessions should use get or create
# Search results instead of pending duo sessions - done
# for node in results - done
# if time almost expiry and is active - done
# if result is none, partially refund user update stats
# Get closest node
# create pair partner functions, returns party_b or none
# get winners func, run ewma, results none: if both parties
# if response not none, add part_b to pop list
# remove nodes from queues, set false
# if winner, reward_winner, update stats
# else fully_refund user, update stats
# Do transactions
# On create set, result as false
# Send message
