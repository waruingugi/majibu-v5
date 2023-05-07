from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.core.config import templates
from app.users.models import User
from app.core.deps import get_current_active_user
from app.core.logger import LoggingRoute


router = APIRouter(route_class=LoggingRoute)
template_prefix = "accounts/templates/"


@router.get("/wallet/", response_class=HTMLResponse)
async def get_wallet(
    request: Request,
    _: User = Depends(get_current_active_user),
):
    """Get wallet page"""
    return templates.TemplateResponse(
        f"{template_prefix}wallet.html",
        {"request": request, "title": "Wallet"},
    )


@router.get("/deposit/", response_class=HTMLResponse)
async def get_deposit(
    request: Request,
    _: User = Depends(get_current_active_user),
):
    """Get deposit page"""
    return templates.TemplateResponse(
        f"{template_prefix}deposit.html",
        {"request": request, "title": "Deposit"},
    )


@router.get("/withdraw/", response_class=HTMLResponse)
async def get_withdraw(
    request: Request,
    _: User = Depends(get_current_active_user),
):
    """Get withdraw page"""
    return templates.TemplateResponse(
        f"{template_prefix}withdraw.html",
        {"request": request, "title": "Withdraw"},
    )


# Navbar Account balance
# Deposit
# Models
# Test models
# Account - mpesa
# Protect docs
# Opening soon template run on close
# Top banner to join whatsapp group - comming soon
# No more sessions
# Host on heroku, buy domain
# Create models
# Create tests
# Create serializers
