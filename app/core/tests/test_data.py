from datetime import datetime
from app.core.utils import Node


node_args = {
    "user_id": None,
    "session_id": None,
    "score": None,
    "is_active": True,
    "expires_at": datetime.now(),
    "win_ratio": 0,
}

no_nodes = []
one_node = [(70, Node(**node_args))]
two_nodes = [(70, Node(**node_args)), (72, Node(**node_args))]
four_nodes = [
    (70, Node(**node_args)),
    (72, Node(**node_args)),
    (78, Node(**node_args)),
    (84, Node(**node_args)),
]
