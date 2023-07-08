from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.users.models import User
from app.quiz.utils import GetSessionQuestions
from app.core.config import templates
from app.core.deps import (
    get_current_active_user,
    get_db,
)
from app.core.logger import LoggingRoute


router = APIRouter(route_class=LoggingRoute)
template_prefix = "quiz/templates/"


@router.get("/questions/{result_id}", response_class=HTMLResponse)
async def get_questions(
    request: Request,
    result_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
    get_session_questions=Depends(GetSessionQuestions),
):
    """Get questions and choices page"""
    quiz = get_session_questions(result_id=result_id)

    return templates.TemplateResponse(
        f"{template_prefix}questions.html",
        {"request": request, "title": "Quiz", "quiz": quiz},
    )


# Remove docs
# Route: receive result_id
# Fetch session_id
# Fetch questions, and choices
# Return questions, and choices
# If time is expired on get request, raise error


# On submission
# Check if time is valid, not expired
# If expired, raise can not be submitted due to time out
# Or penalize heavily with the greater the time submitted
# Calculate results, save to db
# Is active true column in results db: it means was played within last 30 minutes
# Once paired or refunded create duo session with appropriate status
