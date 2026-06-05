from app.crud.auth import *
from typing import Annotated
from fastapi import Path, Request
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_required import token_required
from app.utils.limiter import limiter, register_limiter
from app.api.v1.schemas.auth_schema import AuthCreate, Signin, ResetPassword

router = APIRouter()

@router.get("/app-wait-users/{start}/{end}")
@limiter.limit("100/second")
async def get_app_wait_users_end(
    request: Request,
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await app_wait_users(db, start, end)

@router.post("/signup")
@limiter.limit("20/minute")
async def signup_endpoint(
    request: Request,
    form_data: Annotated[AuthCreate, Depends(AuthCreate.as_form)],
    db: AsyncSession = Depends(get_db)
):
    return await signup(form_data, db)

@router.post("/create-admin")
@limiter.limit("20/minute")
async def create_admin_endpoint(
    request: Request,
    form_data: Annotated[AuthCreate, Depends(AuthCreate.as_form)],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await create_admin(form_data, db)

@router.post("/signin")
@limiter.limit("10/minute")
async def signin_endpoint(
    request: Request,
    credentials: Signin,
    db: AsyncSession = Depends(get_db)
):
    return await signin(credentials,db)

@router.post("/approve-user/{fin_kod}")
@limiter.limit("200/minute")
async def approve_user_endpoint(
    request: Request,
    fin_kod: Annotated[str, Path(..., description="Fin Kod")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await approve_user(fin_kod, db)

@router.post("/send-otp/{fin_kod}")
@limiter.limit("5/minute")
async def send_otp_endpoint(
    request: Request,
    fin_kod: Annotated[str, Path(..., description="Fin Kod")],
    db: AsyncSession = Depends(get_db),
):
    return await send_otp(fin_kod, db)

@router.post("/validate-otp/{fin_kod}/{otp}")
@limiter.limit("10/minute")
async def validate_otp_endpoint(
    request: Request,
    fin_kod: Annotated[str, Path(..., description="Fin Kod")],
    otp: Annotated[str, Path(..., description="OTP")],
    db: AsyncSession = Depends(get_db),
):
    return await validate_otp(fin_kod, otp, db)

@router.post("/reset-password")
@limiter.limit("10/minute")
async def reset_pass_endpoint(
    request: Request,
    reset_data: ResetPassword,
    db: AsyncSession = Depends(get_db)
):
    return await reset_password(reset_data, db)

@router.delete("/reject-user/{fin_kod}")
@limiter.limit("200/minute")
async def approve_user_endpoint(
    request: Request,
    fin_kod: Annotated[str, Path(..., description="Fin Kod")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await reject_app_user(fin_kod, db)