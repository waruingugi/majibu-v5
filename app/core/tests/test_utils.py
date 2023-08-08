import heapq
import itertools
import random

from typing import Callable
from pytest_mock import MockerFixture
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.commons.utils import generate_uuid
from app.core.config import settings
from app.core.utils import PairUsers, Node
from app.core.logger import logger
from app.core.tests.test_data import (
    no_nodes,
    one_node,
    two_nodes,
    four_nodes,
)
from app.sessions.daos.session import pool_session_stats_dao
from app.sessions.serializers.session import PoolSessionStatsCreateSerializer


def test_create_nodes_returns_correct_ordered_score_list(
    mocker: MockerFixture,
    create_result_instances_to_be_paired: Callable,
) -> None:
    """Assert that PairUsers class creates an ordered list of scores"""
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        minutes=settings.SESSION_DURATION
    )

    pair_users = PairUsers()
    ordered_score_list = pair_users.ordered_scores_list

    for elem in range(1, len(ordered_score_list)):
        assert ordered_score_list[elem - 1][0] <= ordered_score_list[elem][0]


def test_create_nodes_returns_correctly_ordered_queue(
    mocker: MockerFixture,
    create_result_instances_to_be_paired: Callable,
) -> None:
    """Assert that PairUsers class creates an ordered FIFO queue of results based on expiry_time"""
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        minutes=settings.SESSION_DURATION
    )

    pair_users = PairUsers()
    results_queue = pair_users.results_queue
    smallest_elem = heapq.heappop(results_queue)

    for elem in results_queue:
        next_smallest_elem = heapq.heappop(results_queue)
        assert smallest_elem < next_smallest_elem
        smallest_elem = next_smallest_elem


def test_create_nodes_returns_empty_list_and_queue(
    create_result_instances_to_be_paired: Callable,
) -> None:
    pair_users = PairUsers()
    results_queue = pair_users.results_queue
    ordered_score_list = pair_users.ordered_scores_list

    assert len(results_queue) == 0
    assert len(ordered_score_list) == 0


def test_get_closest_nodes_returns_correct_node_siblings(mocker: MockerFixture) -> None:
    """Assert that the nodes closest to a given score, are indeed the closest/correct nodes."""
    logger.warning("Starting computationally expensive test. This may take a minute...")

    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)
    target_score = random.randint(
        int(settings.MODERATED_LOWEST_SCORE), int(settings.MODERATED_HIGHEST_SCORE)
    )
    session_ids = [
        generate_uuid() for _ in range(5)
    ]  # 5 is just a random low int to ensure
    # some results nodes at least have the same session
    target_node = Node(
        user_id=None,
        session_id=random.choice(session_ids),
        score=target_score,
        expires_at=datetime.now(),
        is_active=True,
        win_ratio=0,
    )

    def generate_combinations():
        # Create a list with a unique set of numbers in a given range
        all_numbers = list(
            range(
                int(settings.MODERATED_LOWEST_SCORE),
                int(settings.MODERATED_HIGHEST_SCORE),
            )
        )

        min_list_length, max_list_length = 1, 6
        # Generate all possible lengths of the list with the set of numbers above
        for length in range(min_list_length, max_list_length):
            # Find all combinations of the remaining numbers of the given length
            for combination in itertools.product(all_numbers, repeat=length):
                # Ensure target_score is present in the combination
                # target_score is just a random score, you can use any score you like as long
                # as it's withing the moderated score range
                if target_score not in combination:
                    continue

                # Create a list of tuples with each number and a blank Node object
                result_list = [
                    (
                        num,
                        Node(
                            user_id=None,
                            session_id=random.choice(session_ids),
                            score=num,
                            expires_at=datetime.now(),
                            is_active=True,
                            win_ratio=0,
                        ),
                    )
                    for num in combination
                ]

                # Sort the list of tuples based on the first element (the score)
                result_list.sort(key=lambda tup: tup[0])
                yield result_list

    all_combinations = list(generate_combinations())
    logger.warning(f"Testing {len(all_combinations)} combinations")

    for combination in all_combinations:
        pair_users = PairUsers()
        pair_users.ordered_scores_list = combination

        closest_nodes = pair_users.get_closest_nodes(target_node)

        if closest_nodes.right_node is not None:
            assert closest_nodes.right_node[1].score >= target_score
            assert closest_nodes.right_node[1].session_id == target_node.session_id

        if closest_nodes.left_node is not None:
            assert closest_nodes.left_node[1].score <= target_score
            assert closest_nodes.left_node[1].session_id == target_node.session_id


def test_calculate_mean_pairwise_difference_returns_correct_values(
    mocker: MockerFixture,
) -> None:
    """Assert that the function returns correct mean pair-wise diff. based on the length of the list"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)
    pair_users = PairUsers()

    pair_users.ordered_scores_list = one_node
    assert pair_users.calculate_mean_pairwise_difference() is None

    pair_users.ordered_scores_list = two_nodes
    assert pair_users.calculate_mean_pairwise_difference() == 2

    pair_users.ordered_scores_list = four_nodes
    assert pair_users.calculate_mean_pairwise_difference() == 4.666666666666667


def test_calculate_average_score_returns_correct_value(
    mocker: MockerFixture,
) -> None:
    """Assert that the func returns correct values"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)
    pair_users = PairUsers()

    pair_users.ordered_scores_list = no_nodes
    assert pair_users.calculate_average_score() is None

    pair_users.ordered_scores_list = four_nodes
    assert pair_users.calculate_average_score() == 76


def test_calculate_exp_weighted_moving_average_returns_average(
    db: Session,
    mocker: MockerFixture,
) -> None:
    """Assert the function returns avrage score if there's no previous EWMA"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)
    pair_users = PairUsers()

    pair_users.ordered_scores_list = four_nodes
    assert pair_users.calculate_exp_weighted_moving_average() == 76

    pair_users.ordered_scores_list = no_nodes
    assert pair_users.calculate_exp_weighted_moving_average() == 0


def test_calculate_exp_weighted_moving_average_returns_correct_ewma(
    db: Session,
    mocker: MockerFixture,
) -> None:
    """Assert the function returns correct exponentially moving weighted average"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)
    pool_session_stats_dao.create(
        db,
        obj_in=PoolSessionStatsCreateSerializer(
            total_players=2,
            average_score=72,
            mean_pairwise_difference=2,
            exp_weighted_moving_average=72,
        ),
    )
    pair_users = PairUsers()

    pair_users.ordered_scores_list = four_nodes
    new_ewma = (settings.EWMA_MIXING_PARAMETER * 76) + (
        1 - settings.EWMA_MIXING_PARAMETER
    ) * 72

    assert pair_users.calculate_exp_weighted_moving_average() == new_ewma
