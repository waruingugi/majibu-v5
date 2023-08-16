from datetime import datetime
from app.commons.utils import generate_uuid
from app.commons.constants import Categories
from app.core.serializers.core import ResultNode


node_args = {
    "id": None,
    "score": None,
    "user_id": None,
    "is_active": True,
    "category": None,
    "session_id": None,
    "expires_at": datetime.now(),
}


no_nodes = []
one_node = [(70, ResultNode(**node_args))]
two_nodes = [(70, ResultNode(**node_args)), (72, ResultNode(**node_args))]
four_nodes = [
    (70, ResultNode(**node_args)),
    (72, ResultNode(**node_args)),
    (78, ResultNode(**node_args)),
    (84, ResultNode(**node_args)),
]


"""Not that changing the score(or category) in result nodes will result in some tests failing
because the results are hardcoded.
In case you want to change a result_node score(or category),
either update the tests or use a new result_node with a different score"""
no_result_nodes = []
one_result_node = [
    ResultNode(
        is_active=True,
        id=generate_uuid(),
        score=70,
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=Categories.BIBLE.value,
    ),
]
two_result_nodes = [
    ResultNode(
        is_active=True,
        id=generate_uuid(),
        score=70,
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=Categories.BIBLE.value,
    ),
    ResultNode(
        is_active=True,
        id=generate_uuid(),
        score=72,
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=Categories.BIBLE.value,
    ),
]
four_result_nodes = [
    ResultNode(
        is_active=True,
        id=generate_uuid(),
        score=70,
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=Categories.BIBLE.value,
    ),
    ResultNode(
        is_active=True,
        id=generate_uuid(),
        score=72,
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=Categories.BIBLE.value,
    ),
    ResultNode(
        is_active=True,
        id=generate_uuid(),
        score=78,
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=Categories.BIBLE.value,
    ),
    ResultNode(
        is_active=True,
        id=generate_uuid(),
        score=84,
        user_id=generate_uuid(),
        expires_at=datetime.now(),
        session_id=generate_uuid(),
        category=Categories.BIBLE.value,
    ),
]
