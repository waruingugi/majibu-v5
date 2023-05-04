from fastapi import APIRouter

from app.accounts.routes import account

router = APIRouter(prefix="/accounts", tags=["accounts"])
router.include_router(account.router)
