from fastapi import Request, APIRouter, Form
from fastapi.responses import HTMLResponse
from typing import Annotated

from app.auth.utils import templates

router = APIRouter()


@router.get("/validate-phone/", response_class=HTMLResponse)
async def get_phone_verification(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/validate-phone/", response_class=HTMLResponse)
async def post_phone_verificationin(request: Request, phone: Annotated[str, Form()]):
    return templates.TemplateResponse("login.html", {"request": request})


# Validate phone no
# On post, create OTP, send OTP
# save number to redis
# Save otp secret, e.t.c to redis
# Redirect to verify otp
# On OTP post, fetch redis
# If valid, generate access token
# redirect to home page
# If not valid, return to validation page
