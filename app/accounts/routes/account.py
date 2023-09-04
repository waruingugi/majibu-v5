from fastapi import Request, APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import phonenumbers

from app.users.models import User
from app.errors.custom import ErrorCodes
from app.accounts.serializers.account import DepositSerializer, WithdrawSerializer
from app.accounts.utils import (
    trigger_mpesa_stkpush_payment,
    process_mpesa_stk,
    process_mpesa_paybill_payment,
    process_b2c_payment,
    process_b2c_payment_result,
)
from app.accounts.daos.account import transaction_dao
from app.accounts.serializers.mpesa import (
    MpesaPaymentResultSerializer,
    MpesaDirectPaymentSerializer,
    WithdrawalResultSerializer,
)
from app.accounts.constants import MPESA_WHITE_LISTED_IPS

from app.core.helpers import md5_hash
from app.core.raw_logger import logger
from app.core.logger import LoggingRoute
from app.core.ratelimiter import limiter
from app.core.config import templates, settings, redis
from app.core.deps import get_current_active_user, get_db

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
    transaction_history = transaction_dao.search(
        db, {"order_by": ["-created_at"], "account": user.phone}
    )[
        :7
    ]  # Show only 7 transactions due to design limitations

    return templates.TemplateResponse(
        f"{template_prefix}wallet.html",
        {
            "request": request,
            "title": "Wallet",
            "current_balance": wallet_balance,
            "transaction_history": transaction_history,
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
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    deposit: DepositSerializer = Depends(),
):
    """Post deposit amount page: User makes this post to receive an STKPush on their device"""
    background_tasks.add_task(
        trigger_mpesa_stkpush_payment, amount=deposit.amount, phone_number=user.phone
    )

    # data = trigger_mpesa_stkpush_payment(amount=deposit.amount, phone_number=user.phone)

    # if data is not None:
    #     # Save the checkout response to db for future reference
    #     mpesa_payment_dao.create(
    #         db,
    #         obj_in=MpesaPaymentCreateSerializer(
    #             phone_number=user.phone,
    #             merchant_request_id=data["MerchantRequestID"],
    #             checkout_request_id=data["CheckoutRequestID"],
    #             response_code=data["ResponseCode"],
    #             response_description=data["ResponseDescription"],
    #             customer_message=data["CustomerMessage"],
    #         ),
    #     )

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


@router.post("/withdraw/", response_class=HTMLResponse)
async def post_withdraw(
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    withdraw: WithdrawSerializer = Depends(),
):
    """Request withdrawal amount"""
    user_balance = transaction_dao.get_user_balance(db, account=user.phone)
    total_withdraw_charge = settings.MPESA_B2C_CHARGE + withdraw.amount

    if user_balance < total_withdraw_charge:
        withdraw.field_errors.append(
            f"You do not have sufficient balance to withdraw ksh{withdraw.amount}"
        )

    elif redis.get(md5_hash(f"{user.phone}:withdraw_request")):
        withdraw.field_errors.append(ErrorCodes.SIMILAR_WITHDRAWAL_REQUEST.value)

    else:
        background_tasks.add_task(
            process_b2c_payment, db, user=user, amount=withdraw.amount
        )
        redirect_url = request.url_for("get_withdraw_success", amount=withdraw.amount)

        return RedirectResponse(
            redirect_url, status_code=302, background=background_tasks
        )

    return templates.TemplateResponse(
        f"{template_prefix}withdraw.html",
        {
            "request": request,
            "title": "Withdraw",
            "field_errors": withdraw.field_errors,
        },
    )


@router.get("/withdraw/success/{amount}", response_class=HTMLResponse)
async def get_withdraw_success(
    request: Request,
    amount: int,
    _: User = Depends(get_current_active_user),
):
    """Get withdraw success page"""
    return templates.TemplateResponse(
        f"{template_prefix}withdraw_success.html",
        {"request": request, "title": "Withdraw", "amount": amount},
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
    logger.info(f"Received STKPush callback request from {request.headers}")
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
    logger.info(f"Received Paybill payment confirmation request from {request.headers}")
    if request.client.host not in MPESA_WHITE_LISTED_IPS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    background_tasks.add_task(process_mpesa_paybill_payment, db, paybill_response_in)


@router.post("/payments/result/")
async def post_withdrawal_result(
    request: Request,
    withdrawal_response_in: WithdrawalResultSerializer,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Callback URL to receive response after posting withdrawal request to M-Pesa"""
    if request.client.host not in MPESA_WHITE_LISTED_IPS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    background_tasks.add_task(
        process_b2c_payment_result, db, withdrawal_response_in.Result
    )


@router.post("/payments/timeout/")
async def post_withdrawal_time_out(
    request: Request,
):
    """
    Callback URL to receive response after posting
    withdrawal request to M-Pesa in case of time out"""
    pass
