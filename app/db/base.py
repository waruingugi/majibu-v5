# Import all the models, so that Base has them before being
# imported by Alembic
from app.auth.models import *  # noqa
from app.users.models import *  # noqa
from app.notifications.models import *  # noqa
from app.sessions.models import *  # noqa
from app.quiz.models import *  # noqa
from app.accounts.models import *  # noqa
from app.db.base_class import Base  # noqa
