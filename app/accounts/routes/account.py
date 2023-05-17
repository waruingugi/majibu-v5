from fastapi import Request, APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import phonenumbers

from app.core.config import templates, settings
from app.users.models import User
from app.accounts.serializers.account import DepositSerializer
from app.accounts.utils import (
    trigger_mpesa_stkpush_payment,
    process_mpesa_stk,
    process_mpesa_paybill_payment,
)
from app.accounts.daos.mpesa import mpesa_payment_dao
from app.accounts.daos.account import transaction_dao
from app.core.deps import get_current_active_user, get_db
from app.accounts.serializers.mpesa import (
    MpesaPaymentCreateSerializer,
    MpesaPaymentResultSerializer,
    MpesaDirectPaymentSerializer,
)
from app.core.logger import LoggingRoute
from app.core.ratelimiter import limiter
from app.accounts.constants import MPESA_WHITE_LISTED_IPS

router = APIRouter(route_class=LoggingRoute)
template_prefix = "accounts/templates/"


@router.get("/wallet/", response_class=HTMLResponse)
async def get_wallet(
    request: Request,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get wallet page"""
    wallet_balance = transaction_dao.get_user_balance(db, account=user.phone)

    return templates.TemplateResponse(
        f"{template_prefix}wallet.html",
        {
            "request": request,
            "title": "Wallet",
            "current_balance": wallet_balance,
        },
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
@limiter.limit("5/minute")
async def post_deposit(
    request: Request,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    deposit: DepositSerializer = Depends(),
):
    """Post deposit amount page"""
    data = trigger_mpesa_stkpush_payment(amount=deposit.amount, phone_number=user.phone)

    if data is not None:
        # Save the checkout response to db for future reference
        mpesa_payment_dao.create(
            db,
            obj_in=MpesaPaymentCreateSerializer(
                phone_number=user.phone,
                merchant_request_id=data["MerchantRequestID"],
                checkout_request_id=data["CheckoutRequestID"],
                response_code=data["ResponseCode"],
                response_description=data["ResponseDescription"],
                customer_message=data["CustomerMessage"],
            ),
        )

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
async def post_callback(
    request: Request,
    *,
    mpesa_response_in: MpesaPaymentResultSerializer,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """CallBack URL is used to receive responses for STKPush from M-Pesa"""
    if request.client.host not in MPESA_WHITE_LISTED_IPS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    background_tasks.add_task(process_mpesa_stk, db, mpesa_response_in.Body.stkCallback)


@router.post("/payments/confirmation/")
async def post_confirmation(
    request: Request,
    paybill_response_in: MpesaDirectPaymentSerializer,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Confirmation URL is used to receive responses for direct paybill payments from M-Pesa"""
    if request.client.host not in MPESA_WHITE_LISTED_IPS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    background_tasks.add_task(process_mpesa_paybill_payment, db, paybill_response_in)


# Callback for paybill
# Serializer for paybill - corrections
# Transactions model create - if valid
# Tests and more tests
# B2C
# Deposit history
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
