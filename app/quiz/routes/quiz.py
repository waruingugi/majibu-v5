from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

# from app.users.models import User
# from app.quiz.utils import GetSessionQuestions
from app.core.config import templates
from app.core.deps import (
    # get_current_active_user,
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
    # user: User = Depends(get_current_active_user),
    # get_session_questions=Depends(GetSessionQuestions),
):
    """Get questions and choices page"""
    # quiz = get_session_questions(result_id=result_id)
    quiz = {
        "Which of these is the first book in the Bible?": [
            "Exodus",
            "Genesis",
            "Leviticus",
        ],
        "Who was the disciple known as 'Doubting Thomas'?": [
            "Peter",
            "Andrew",
            "Thomas",
        ],
        "What is the last book of the New Testament?": [
            "Revelation",
            "Acts",
            "Galatians",
        ],
        "Who led the Israelites out of Egypt?": ["Moses", "Joshua", "Aaron"],
        "Which of these is not one of the Ten Commandments?": [
            "You shall not covet",
            "You shall not murder",
            "You shall not love your neighbor as yourself",
        ],
    }

    return templates.TemplateResponse(
        f"{template_prefix}questions.html",
        {"request": request, "title": "Quiz", "quiz": quiz},
    )


@router.post("/answers/{result_id}", response_class=HTMLResponse)
async def post_answers(
    request: Request,
    result_id: str,
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_active_user),
    # get_session_questions=Depends(GetSessionQuestions),
):
    import pdb

    pdb.set_trace()
    quiz = {
        "Which of these is the first book in the Bible?": [
            "Exodus",
            "Genesis",
            "Leviticus",
        ],
        "Who was the disciple known as 'Doubting Thomas'?": [
            "Peter",
            "Andrew",
            "Thomas",
        ],
        "What is the last book of the New Testament?": [
            "Revelation",
            "Acts",
            "Galatians",
        ],
        "Who led the Israelites out of Egypt?": ["Moses", "Joshua", "Aaron"],
        "Which of these is not one of the Ten Commandments?": [
            "You shall not covet",
            "You shall not murder",
            "You shall not love your neighbor as yourself",
        ],
    }

    return templates.TemplateResponse(
        f"{template_prefix}questions.html",
        {"request": request, "title": "Quiz", "quiz": quiz},
    )


# Remove docs
# If time is expired on get request, raise error


# On submission
# Check if time is valid, not expired
# If expired, raise can not be submitted due to time out
# Or penalize heavily with the greater the time submitted
# Calculate results, save to db
# Is active true column in results db: it means was played within last 30 minutes
# Once paired or refunded create duo session with appropriate status
