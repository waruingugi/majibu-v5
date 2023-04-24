from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.core.config import templates
from app.users.models import User
from app.core.deps import get_current_active_user


router = APIRouter()
template_prefix = "sessions/templates/"


@router.get("/home/", response_class=HTMLResponse)
async def get_home(
    request: Request,
    _: User = Depends(get_current_active_user),
):
    """Get home page"""
    return templates.TemplateResponse(
        f"{template_prefix}home.html", {"request": request}
    )
