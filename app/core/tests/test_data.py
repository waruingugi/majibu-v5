from datetime import datetime
from app.core.serializers.core import ResultNode


node_args = {
    "user_id": None,
    "session_id": None,
    "score": None,
    "is_active": True,
    "expires_at": datetime.now(),
    "win_ratio": 0,
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
