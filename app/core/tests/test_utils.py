import heapq
import itertools
import random

from typing import Callable
from pytest_mock import MockerFixture
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.commons.utils import generate_uuid
from app.core.config import settings
from app.core.utils import PairUsers
from app.core.serializers.core import (
    ResultNode,
    ClosestNodeSerializer,
    PairPartnersSerializer,
)
from app.core.raw_logger import logger
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
    target_node = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=random.choice(session_ids),
        score=target_score,
        expires_at=datetime.now(),
        is_active=True,
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
                        ResultNode(
                            id=generate_uuid(),
                            user_id=generate_uuid(),
                            session_id=random.choice(session_ids),
                            score=num,
                            expires_at=datetime.now(),
                            is_active=True,
                        ),
                    )
                    for num in combination
                ]

                # Sort the list of tuples based on the first element (the score)
                result_list.sort(key=lambda tup: tup[0])
                yield result_list

    all_combinations = list(generate_combinations())

    # Set all logs from this point forward to WARNING so that they are visible in the terminal
    pair_users = PairUsers()

    logger.warning(f"Testing {len(all_combinations)} combinations")
    for combination in all_combinations:
        pair_users.ordered_scores_list = combination

        closest_nodes = pair_users.get_closest_nodes(target_node)

        if closest_nodes.right_node is not None:
            assert closest_nodes.right_node.score >= target_score
            assert closest_nodes.right_node.session_id == target_node.session_id
            assert closest_nodes.right_node.user_id != target_node.user_id

        if closest_nodes.left_node is not None:
            assert closest_nodes.left_node.score <= target_score
            assert closest_nodes.left_node.session_id == target_node.session_id
            assert closest_nodes.left_node.user_id != target_node.user_id


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


def test_calculate_exp_weighted_moving_average_returns_mean_pairwise_diff(
    db: Session,
    mocker: MockerFixture,
) -> None:
    """Assert the function returns avrage score if there's no previous EWMA"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)
    pair_users = PairUsers()

    pair_users.ordered_scores_list = four_nodes
    assert pair_users.calculate_exp_weighted_moving_average() == 4.666666666666667

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
            mean_pairwise_difference=3,
            exp_weighted_moving_average=2,
        ),
    )
    pair_users = PairUsers()
    pair_users.ordered_scores_list = four_nodes

    assert pair_users.calculate_exp_weighted_moving_average() == 3.8666666666666667


def test_set_pool_session_statistics_saves_instance_to_model(
    db: Session,
    mocker: MockerFixture,
    delete_pool_session_stats_model_instances: Callable,
    create_result_instances_to_be_paired: Callable,
) -> None:
    """Assert the function creates a PoolSessionStats instance"""
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        minutes=settings.SESSION_DURATION
    )

    pair_users = PairUsers()
    pair_users.set_pool_session_statistics()

    pool_session_obj = pool_session_stats_dao.get(db)

    assert pool_session_obj is not None


def test_get_pair_partner_returns_correct_node_when_both_have_same_score(
    mocker: MockerFixture,
) -> None:
    """Assert function returns any partner node when:
    - Both right node and left node are not None
    - Right node and left node both have the same score"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)
    same_score = 74
    same_score_list = [same_score, same_score]
    target_node = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=same_score + 2,
        expires_at=datetime.now(),
        is_active=True,
    )

    result_nodes_list = [
        ResultNode(
            id=generate_uuid(),
            user_id=generate_uuid(),
            session_id=generate_uuid(),
            score=num,
            expires_at=datetime.now(),
            is_active=True,
        )
        for num in same_score_list
    ]
    closeest_nodes_in = ClosestNodeSerializer(
        left_node=result_nodes_list[0], right_node=result_nodes_list[1]
    )

    pair_users = PairUsers()
    partner = pair_users.get_pair_partner(target_node, closeest_nodes_in)

    assert partner in result_nodes_list


def test_get_pair_partner_returns_correct_node_when_right_node_is_closer_to_target_node(
    mocker: MockerFixture,
) -> None:
    """Assert function returns correct partner node when:
    - Both right node and left node are not None
    - But the right node is closer to the target node"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    score_list = [72, 78]
    target_node = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=76,  # Score is closer to the right node
        expires_at=datetime.now(),
        is_active=True,
    )

    result_nodes_list = [
        ResultNode(
            id=generate_uuid(),
            user_id=generate_uuid(),
            session_id=generate_uuid(),
            score=num,
            expires_at=datetime.now(),
            is_active=True,
        )
        for num in score_list
    ]

    left_node = result_nodes_list[0]
    right_node = result_nodes_list[1]

    closeest_nodes_in = ClosestNodeSerializer(
        left_node=left_node, right_node=right_node
    )

    pair_users = PairUsers()
    partner = pair_users.get_pair_partner(target_node, closeest_nodes_in)

    assert partner == right_node


def test_get_pair_partner_returns_correct_node_when_left_node_is_closer_to_target_node(
    mocker: MockerFixture,
) -> None:
    """Assert function returns correct partner node when:
    - Both right node and left node are not None
    - But the left node is closer to the target node"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    score_list = [74, 76]
    target_node = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=72,  # Score is closer to the left node
        expires_at=datetime.now(),
        is_active=True,
    )

    result_nodes_list = [
        ResultNode(
            id=generate_uuid(),
            user_id=generate_uuid(),
            session_id=generate_uuid(),
            score=num,
            expires_at=datetime.now(),
            is_active=True,
        )
        for num in score_list
    ]

    left_node = result_nodes_list[0]
    right_node = result_nodes_list[1]

    closeest_nodes_in = ClosestNodeSerializer(
        left_node=left_node, right_node=right_node
    )

    pair_users = PairUsers()
    partner = pair_users.get_pair_partner(target_node, closeest_nodes_in)

    assert partner == left_node


def test_get_pair_partner_returns_correct_node_when_left_node_only_exists(
    mocker: MockerFixture,
) -> None:
    """Assert function returns correct partner node when:
    - Only the left node exists"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    target_node = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=74,  # Score is closer to the left node
        expires_at=datetime.now(),
        is_active=True,
    )

    left_node = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=72,
        expires_at=datetime.now(),
        is_active=True,
    )

    closeest_nodes_in = ClosestNodeSerializer(left_node=left_node, right_node=None)

    pair_users = PairUsers()
    partner = pair_users.get_pair_partner(target_node, closeest_nodes_in)

    assert partner == left_node


def test_get_pair_partner_returns_correct_node_when_right_node_only_exists(
    mocker: MockerFixture,
) -> None:
    """Assert function returns correct partner node when:
    - Only the right node exists"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    target_node = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=72,  # Score is closer to the left node
        expires_at=datetime.now(),
        is_active=True,
    )

    right_node = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=74,
        expires_at=datetime.now(),
        is_active=True,
    )

    closeest_nodes_in = ClosestNodeSerializer(left_node=None, right_node=right_node)

    pair_users = PairUsers()
    partner = pair_users.get_pair_partner(target_node, closeest_nodes_in)

    assert partner == right_node


def test_get_pair_partner_returns_none_when_no_node_exists(
    mocker: MockerFixture,
) -> None:
    """Assert function returns None when:
    - No partner node exists"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    target_node = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=72,  # Score is closer to the left node
        expires_at=datetime.now(),
        is_active=True,
    )

    closeest_nodes_in = ClosestNodeSerializer(left_node=None, right_node=None)

    pair_users = PairUsers()
    partner = pair_users.get_pair_partner(target_node, closeest_nodes_in)

    assert partner is None


def test_get_winner_returns_party_a_as_winner(
    mocker: MockerFixture,
) -> None:
    """Assert that the function returns party_a as the winner"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    party_a = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=74,  # Score is closer to the left node
        expires_at=datetime.now(),
        is_active=True,
    )

    party_b = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=72,
        expires_at=datetime.now(),
        is_active=True,
    )

    pair_users = PairUsers()
    """Pairing range should be less than the difference between party_a score and party_b score
    to enable pairing"""
    pair_users.pairing_range = 3
    pair_partner_in = PairPartnersSerializer(party_a=party_a, party_b=party_b)
    winner = pair_users.get_winner(pair_partner_in)

    assert winner == party_a


def test_get_winner_returns_party_b_as_winner(
    mocker: MockerFixture,
) -> None:
    """Assert that the function returns party_b as the winner"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    party_a = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=72,  # Score is closer to the left node
        expires_at=datetime.now(),
        is_active=True,
    )

    party_b = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=74,
        expires_at=datetime.now(),
        is_active=True,
    )

    pair_users = PairUsers()
    """Pairing range should be less than the difference between party_a score and party_b score
    to enable pairing"""
    pair_users.pairing_range = 3
    pair_partner_in = PairPartnersSerializer(party_a=party_a, party_b=party_b)
    winner = pair_users.get_winner(pair_partner_in)

    assert winner == party_b


def test_get_winner_returns_no_winner(
    mocker: MockerFixture,
) -> None:
    """Assert that the function returns no winner when both partners are not within pairing range"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    party_a = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=74,  # Score is closer to the left node
        expires_at=datetime.now(),
        is_active=True,
    )

    party_b = ResultNode(
        id=generate_uuid(),
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        score=72,
        expires_at=datetime.now(),
        is_active=True,
    )

    pair_users = PairUsers()
    """Pairing range should be less than the difference between party_a score and party_b score
    to enable pairing"""
    pair_users.pairing_range = 1
    pair_partner_in = PairPartnersSerializer(party_a=party_a, party_b=party_b)
    winner = pair_users.get_winner(pair_partner_in)

    assert winner is None
