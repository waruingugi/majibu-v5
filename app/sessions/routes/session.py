from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse

from app.core.config import templates


router = APIRouter()
template_prefix = "sessions/templates/"


@router.get("/home/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Get home page"""
    return templates.TemplateResponse(
        f"{template_prefix}home.html", {"request": request}
    )
