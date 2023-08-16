from datetime import datetime
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
