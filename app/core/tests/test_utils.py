import heapq
from typing import Callable
from pytest_mock import MockerFixture
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.utils import PairUsers


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
