from fastapi import APIRouter

from app.sessions.routes import session

router = APIRouter(prefix="/session", tags=["session"])
router.include_router(session.router)
