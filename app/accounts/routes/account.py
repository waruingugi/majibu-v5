from fastapi import Request, APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
import phonenumbers

from app.core.config import templates, settings
from app.users.models import User
from app.accounts.serializers.account import DepositSerializer
from app.accounts.utils import trigger_mpesa_stkpush_payment
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
    user: User = Depends(get_current_active_user),
):
    """Get deposit page"""
    account = phonenumbers.format_number(
        phonenumbers.parse(user.phone), phonenumbers.PhoneNumberFormat.NATIONAL
    )
    return templates.TemplateResponse(
        f"{template_prefix}deposit.html",
        {
            "request": request,
            "title": "Deposit",
            "account": account,
            "paybill": settings.MPESA_BUSINESS_SHORT_CODE,
        },
    )


@router.post("/deposit/", response_class=HTMLResponse)
async def post_deposit(
    request: Request,
    deposit: DepositSerializer = Depends(),
    user: User = Depends(get_current_active_user),
):
    """Post deposit amount page"""
    trigger_mpesa_stkpush_payment(amount=deposit.amount, phone_number=user.phone)

    redirect_url = request.url_for("get_stkpush")
    return RedirectResponse(redirect_url, status_code=302)


@router.get("/stk/", response_class=HTMLResponse)
async def get_stkpush(
    request: Request,
    _: User = Depends(get_current_active_user),
):
    """Get STKPush page"""
    return templates.TemplateResponse(
        f"{template_prefix}stkpush_sent.html",
        {"request": request, "title": "New message"},
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


@router.post("/payments/callback/")
async def post_confirmation(
    request: Request,
):
    return {"Received": 1}


# If 0 response in stkpush - successfull
# Receives sms on paybill payment
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
