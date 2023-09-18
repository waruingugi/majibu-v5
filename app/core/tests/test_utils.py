import json
import copy
import heapq
import random
import pytest
import itertools

from typing import Callable
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from datetime import datetime, timedelta

from app.users.daos.user import user_dao
from app.users.serializers.user import UserCreateSerializer

from app.quiz.daos.quiz import result_dao
from app.quiz.filters import ResultFilter
from app.quiz.serializers.quiz import ResultCreateSerializer

from app.commons.utils import generate_uuid
from app.commons.constants import Categories

from app.core.config import settings
from app.core.utils import PairUsers
from app.core.serializers.core import (
    ResultNode,
    ClosestNodeSerializer,
    PairPartnersSerializer,
)
from app.core.raw_logger import logger
from app.core.tests.test_data import (
    no_result_nodes,
    one_result_node,
    two_result_nodes,
    four_result_nodes,
)

from app.sessions.filters import SessionFilter
from app.sessions.constants import DuoSessionStatuses
from app.sessions.daos.session import (
    pool_session_stats_dao,
    duo_session_dao,
    session_dao,
)
from app.sessions.serializers.session import (
    PoolCategoryStatistics,
    PoolSessionStatsCreateSerializer,
)


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

    for _ in results_queue:
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


# Run this test as the last one after all others have run because it
# takes time to complete
@pytest.mark.order(index=-1)
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
        is_active=True,
        id=generate_uuid(),
        score=target_score,
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=random.choice(session_ids),
        category=random.choice(Categories.list_()),
    )

    def generate_combinations():
        # Create a list with a unique set of numbers in a given range
        all_numbers = list(
            range(
                int(settings.MODERATED_LOWEST_SCORE),
                int(settings.MODERATED_HIGHEST_SCORE),
            )
        )

        min_list_length, max_list_length = 1, 5
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
                            score=num,
                            id=generate_uuid(),
                            user_id=generate_uuid(),
                            expires_at=datetime.now(),
                            session_id=random.choice(session_ids),
                            category=random.choice(Categories.list_()),
                            is_active=random.choice(
                                [True, False]
                            ),  # A node can be active or not
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

            assert closest_nodes.right_node.is_active is True
            assert closest_nodes.right_node.user_id != target_node.user_id

        if closest_nodes.left_node is not None:
            assert closest_nodes.left_node.score <= target_score
            assert closest_nodes.left_node.session_id == target_node.session_id

            assert closest_nodes.left_node.is_active is True
            assert closest_nodes.left_node.user_id != target_node.user_id


def test_calculate_mean_pairwise_difference_returns_correct_values(
    mocker: MockerFixture,
) -> None:
    """Assert that the function returns correct mean pair-wise diff. based on the length of the list"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)
    pair_users = PairUsers()

    pair_users.results_queue = one_result_node
    assert (
        pair_users.calculate_mean_pairwise_difference(category=Categories.BIBLE.value)
        is None
    )

    pair_users.results_queue = two_result_nodes
    assert (
        pair_users.calculate_mean_pairwise_difference(category=Categories.BIBLE.value)
        == 2
    )

    pair_users.results_queue = four_result_nodes
    assert (
        pair_users.calculate_mean_pairwise_difference(category=Categories.BIBLE.value)
        == 4.666666666666667
    )


def test_calculate_average_score_returns_correct_value(
    mocker: MockerFixture,
) -> None:
    """Assert that the func returns correct values"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)
    pair_users = PairUsers()

    pair_users.results_queue = no_result_nodes
    assert pair_users.calculate_average_score(Categories.BIBLE.value) is None

    # Copy the elements of four_result_nodes to prevent it's modification
    # (Changing four_result_nodes elements affects future tests becauses the variable
    # is initialized only once and used in throughout the tests)
    # And change the last node's category
    new_result_nodes = copy.deepcopy(four_result_nodes)
    new_result_nodes[3].category = Categories.FOOTBALL.value

    pair_users.results_queue = new_result_nodes
    assert (
        pair_users.calculate_average_score(Categories.BIBLE.value) == 73.33333333333333
    )


def test_calculate_average_score_returns_none_if_category_has_no_nodes(
    mocker: MockerFixture,
) -> None:
    """Assert that the fuction returns None(instead of Zero Division error) when
    results_queue does not have nodes with that category"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)
    new_result_nodes = copy.deepcopy(four_result_nodes)

    pair_users = PairUsers()
    pair_users.results_queue = new_result_nodes
    assert pair_users.calculate_average_score(Categories.FOOTBALL.value) is None


def test_calculate_exp_weighted_moving_average_returns_mean_pairwise_diff(
    db: Session,
    mocker: MockerFixture,
    delete_pool_session_stats_model_instances: Callable,
) -> None:
    """Assert the function returns average score if there's no previous EWMA"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)
    pair_users = PairUsers()
    pair_users.results_queue = four_result_nodes

    assert (
        pair_users.calculate_exp_weighted_moving_average(Categories.BIBLE.value)
        == 4.666666666666667
    )

    pair_users.results_queue = no_result_nodes
    assert pair_users.calculate_exp_weighted_moving_average(Categories.BIBLE.value) == 0


def test_calculate_exp_weighted_moving_average_returns_correct_ewma(
    db: Session,
    mocker: MockerFixture,
) -> None:
    """Assert the function returns correct exponentially moving weighted average"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    # Create a previous PoolSessionStat
    category_stats = PoolCategoryStatistics(
        players=3,
        threshold=settings.PAIRING_THRESHOLD,
        mean_paiwise_difference=2,
        pairing_range=2,
        exp_weighted_moving_average=2,
    )
    stats = {}
    stats[Categories.BIBLE.value] = category_stats.dict()

    pool_session_stats_dao.create(
        db,
        obj_in=PoolSessionStatsCreateSerializer(
            total_players=3, statistics=json.dumps(stats)
        ),
    )

    pair_users = PairUsers()
    pair_users.results_queue = four_result_nodes

    assert (
        pair_users.calculate_exp_weighted_moving_average(Categories.BIBLE.value)
        == 3.8666666666666667
    )


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
    assert bool(pair_users.statistics) is not False


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
        is_active=True,
        id=generate_uuid(),
        score=same_score + 2,
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
    )

    result_nodes_list = [
        ResultNode(
            score=num,
            is_active=True,
            id=generate_uuid(),
            user_id=generate_uuid(),
            expires_at=datetime.now(),
            session_id=generate_uuid(),
            category=random.choice(Categories.list_()),
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
        score=76,
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
    )

    result_nodes_list = [
        ResultNode(
            score=num,
            is_active=True,
            id=generate_uuid(),
            user_id=generate_uuid(),
            expires_at=datetime.now(),
            session_id=generate_uuid(),
            category=random.choice(Categories.list_()),
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
        score=72,  # Score is closer to the left node
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
    )

    result_nodes_list = [
        ResultNode(
            score=num,
            is_active=True,
            id=generate_uuid(),
            user_id=generate_uuid(),
            expires_at=datetime.now(),
            session_id=generate_uuid(),
            category=random.choice(Categories.list_()),
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
        score=74,  # Score is closer to the left node
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
    )

    left_node = ResultNode(
        score=72,
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
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
        score=72,  # Score is closer to the left node
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
    )

    right_node = ResultNode(
        score=74,
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
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
        score=72,  # Score is closer to the left node
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
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
        score=74,  # Score is closer to the left node
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
    )

    party_b = ResultNode(
        score=72,
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
    )

    pair_users = PairUsers()
    """Pairing range should be less than the difference between party_a score and party_b score
    to enable pairing"""
    pair_users.statistics = {
        Categories.BIBLE.value: {"pairing_range": 3},
        Categories.FOOTBALL.value: {"pairing_range": 3},
    }

    pair_partner_in = PairPartnersSerializer(party_a=party_a, party_b=party_b)
    winner = pair_users.get_winner(pair_partner_in)

    assert winner == party_a


def test_get_winner_returns_party_b_as_winner(
    mocker: MockerFixture,
) -> None:
    """Assert that the function returns party_b as the winner"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    party_a = ResultNode(
        score=72,  # Score is closer to the left node
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
    )

    party_b = ResultNode(
        score=74,
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
    )

    pair_users = PairUsers()
    """Pairing range should be less than the difference between party_a score and party_b score
    to enable pairing"""
    pair_users.statistics = {
        Categories.BIBLE.value: {"pairing_range": 3},
        Categories.FOOTBALL.value: {"pairing_range": 3},
    }
    pair_partner_in = PairPartnersSerializer(party_a=party_a, party_b=party_b)
    winner = pair_users.get_winner(pair_partner_in)

    assert winner == party_b


def test_get_winner_returns_no_winner(
    mocker: MockerFixture,
) -> None:
    """Assert that the function returns no winner when both partners are not within pairing range"""
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    party_a = ResultNode(
        score=74,
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
    )

    party_b = ResultNode(
        score=72,
        is_active=True,
        id=generate_uuid(),
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=random.choice(Categories.list_()),
    )

    pair_users = PairUsers()
    """Pairing range should be less than the difference between party_a score and party_b score
    to enable pairing"""
    pair_users.statistics = {
        Categories.BIBLE.value: {"pairing_range": 1},
        Categories.FOOTBALL.value: {"pairing_range": 1},
    }
    pair_partner_in = PairPartnersSerializer(party_a=party_a, party_b=party_b)
    winner = pair_users.get_winner(pair_partner_in)

    assert winner is None


def test_create_duo_session_saves_model_instance(
    db: Session,
    mocker: MockerFixture,
    create_user_model_instances: Callable,
    create_session_model_instances: Callable,
    delete_duo_session_model_instances: Callable,
) -> None:
    """Assert ´create_duo_session´ creates model instances"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    mocker.patch("app.core.utils.PairUsers.create_nodes", return_value=None)

    sessions = session_dao.get_all(db)
    session_ids = list(map(lambda x: x.id, sessions))

    users = user_dao.get_all(db)
    user_ids = list(map(lambda x: x.id, users))
    party_a_user_id = user_ids[0]

    duo_session_statuses = DuoSessionStatuses.list_()
    pair_users = PairUsers()

    """Each user can play a session only once, that's why we loop through
    the session ids rather than picking a random choice"""
    session_index = 0
    user_index = 1  # Start from 1 because party_a is users[0]

    for status in duo_session_statuses:
        party_a = ResultNode(
            score=72,
            is_active=True,
            id=generate_uuid(),
            user_id=party_a_user_id,
            expires_at=datetime.now(),
            session_id=session_ids[session_index],
            category=random.choice(Categories.list_()),
        )

        party_b = one_result_node[0]
        party_b.user_id = user_ids[user_index]
        winner = None

        if status == DuoSessionStatuses.PAIRED:
            winner = party_a
        else:
            winner = None
            party_b = None

        pair_users.create_duo_session(
            party_a=party_a, party_b=party_b, winner=winner, duo_session_status=status
        )
        session_index += 1
        user_index += 1

    duo_session_objs = duo_session_dao.get_all(db)

    # Assert that the number of model instances are equal to the number of
    # DuoSessionStatuses
    assert len(duo_session_objs) > 1
    assert len(duo_session_objs) == len(duo_session_statuses)


def test_deactivate_results_runs_successfully(
    db: Session, mocker: MockerFixture, create_result_instances_to_be_paired: Callable
) -> None:
    """Assert that the function deactivates all selected nodes"""
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        minutes=settings.SESSION_DURATION
    )

    results_obj = result_dao.get_all(db)
    no_of_results = len(results_obj)
    pair_users = PairUsers()
    results_queue = pair_users.results_queue

    # Deactivate all elements except one
    pair_users.deactivate_results(results_queue[: no_of_results - 1])

    active_results = len(result_dao.get_all(db, is_active=True))

    active_nodes = 0
    for node in results_queue:
        if node.is_active:
            active_nodes += 1

    assert active_nodes == 1
    assert active_results == 1


def test_calculate_total_players_returns_correct_value(
    db: Session, mocker: MockerFixture, create_result_instances_to_be_paired: Callable
) -> None:
    """Assert that the function correct total players"""
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        minutes=settings.SESSION_DURATION
    )

    pair_users = PairUsers()
    total_players = pair_users.calculate_total_players()
    bible_players = pair_users.calculate_total_players(Categories.BIBLE.value)
    football_players = pair_users.calculate_total_players(Categories.FOOTBALL.value)

    total_bible_players = len(
        result_dao.search(
            db,
            search_filter=ResultFilter(
                session=SessionFilter(category=Categories.BIBLE.value)
            ),
        )
    )

    total_football_players = len(
        result_dao.search(
            db,
            search_filter=ResultFilter(
                session=SessionFilter(category=Categories.FOOTBALL.value)
            ),
        )
    )

    assert football_players == total_football_players
    assert bible_players == total_bible_players
    assert total_players == (total_bible_players + total_football_players)


def test_match_players_creates_a_partially_refunded_session(
    db: Session,
    mocker: MockerFixture,
    delete_duo_session_model_instances: Callable,
    create_result_instances_to_be_paired: Callable,
) -> None:
    """Assert function partially refunds users who did not attempt atleast one question"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        seconds=settings.RESULT_PAIRS_AFTER_SECONDS + 60
    )

    pair_users = PairUsers()
    result_node = pair_users.results_queue[0]

    # Set result_node score to 0.0 so that it's partially refunded
    result_node.score = 0.0

    pair_users.match_players()

    duo_session = duo_session_dao.get_not_none(
        db, party_a=result_node.user_id, session_id=result_node.session_id
    )

    assert duo_session.status == DuoSessionStatuses.PARTIALLY_REFUNDED.value


def test_match_players_creates_a_refunded_session(
    db: Session,
    mocker: MockerFixture,
    delete_duo_session_model_instances: Callable,
    create_result_instances_to_be_paired: Callable,
) -> None:
    """Assert function refunds users when no close partner was found"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        seconds=settings.RESULT_PAIRS_AFTER_SECONDS + 60
    )

    result_objs = result_dao.get_all(db)
    party_a_result = result_objs[0]
    # Set an outrageous high score so that no partner is found
    result_dao.update(db, db_obj=party_a_result, obj_in={"score": 100})

    pair_users = PairUsers()
    pair_users.match_players()

    duo_session = duo_session_dao.get_not_none(
        db, party_a=party_a_result.user_id, session_id=party_a_result.session_id
    )

    assert duo_session.status == DuoSessionStatuses.REFUNDED.value


def test_match_players_creates_a_paired_session(
    db: Session,
    mocker: MockerFixture,
    delete_duo_session_model_instances: Callable,
    create_result_instances_to_be_paired: Callable,
) -> None:
    """Assert function creates a paired DuoSession for users who have very close scores"""
    mocker.patch(  # Mock send_notification so that we don't have to wait for it
        "app.sessions.daos.session.notifications_dao.send_notification",
        return_value=None,
    )
    mock_datetime = mocker.patch("app.core.utils.datetime")
    mock_datetime.now.return_value = datetime.now() + timedelta(
        seconds=settings.RESULT_PAIRS_AFTER_SECONDS + 60
    )

    # Get two users and modify their scores to be super close
    party_b_user = user_dao.get_or_create(
        db, UserCreateSerializer(phone="+254764845040")
    )

    """I noticed that if you don't use the earliest created result as party_a,
    other results may pair with part_b causing this test to fail"""
    result_objs = result_dao.search(db, {"order_by": ["created_at"]})
    party_a_result = result_objs[0]

    # Ensure their session_id is same and their scores are super close
    party_b_result = result_dao.create(
        db,
        obj_in=ResultCreateSerializer(
            user_id=party_b_user.id, session_id=party_a_result.session_id
        ),
    )
    result_dao.update(
        db,
        db_obj=party_a_result,  # type: ignore
        obj_in={  # type: ignore
            "score": 75.112  # System accuracy is only upto 7 digits: settings.SESSION_RESULT_DECIMAL_PLACES
        },
    )
    result_dao.update(
        db,
        db_obj=party_b_result,
        obj_in={
            "score": 75.111  # System accuracy is only upto 7 digits: settings.SESSION_RESULT_DECIMAL_PLACES
        },
    )

    duo_session = None
    pair_users = PairUsers()
    pair_users.match_players()

    duo_session = duo_session_dao.get_not_none(
        db, party_a=party_a_result.user_id, session_id=party_a_result.session_id
    )

    assert duo_session.status == DuoSessionStatuses.PAIRED.value
    assert duo_session.party_b == party_b_result.user_id  # type: ignore
