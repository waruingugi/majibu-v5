from fastapi import APIRouter

from app.quiz.routes import quiz

router = APIRouter(prefix="/quiz", tags=["quiz"])
router.include_router(quiz.router)
