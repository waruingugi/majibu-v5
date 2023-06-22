import uuid


def generate_uuid() -> str:
    """Generate a random UUID"""
    return str(uuid.uuid4())
