from fastapi import APIRouter

from app.auth.routes import login

router = APIRouter(prefix="/auth", tags=["login"])
router.include_router(login.router)
