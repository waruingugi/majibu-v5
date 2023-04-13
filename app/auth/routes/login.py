from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse

from app.auth.utils import templates

router = APIRouter()


@router.get("/login/", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
