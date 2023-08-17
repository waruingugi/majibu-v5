from datetime import datetime
from app.commons.utils import generate_uuid
from app.commons.constants import Categories
from app.core.serializers.core import ResultNode


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
