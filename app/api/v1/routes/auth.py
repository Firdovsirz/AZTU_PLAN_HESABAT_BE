from fastapi import Path
from app.crud.auth import *
from typing import Annotated
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.schemas.auth_schema import AuthCreate, Signin, ResetPassword

router = APIRouter()

@router.post("/signup")
async def signup_endpoint(
    form_data: Annotated[AuthCreate, Depends(AuthCreate.as_form)],
    db: AsyncSession = Depends(get_db)
):
    return await signup(form_data, db)

@router.post("/signin")
async def signin_endpoint(
    credentials: Signin,
    db: AsyncSession = Depends(get_db)
):
    return await signin(credentials,db)

@router.post("/approve-user/{fin_kod}")
async def approve_user_endpoint(
    fin_kod: Annotated[str, Path(..., description="Fin Kod")],
    db: AsyncSession = Depends(get_db)
):
    return await approve_user(fin_kod, db)

@router.delete("/reject-user/{fin_kod}")
async def approve_user_endpoint(
    fin_kod: Annotated[str, Path(..., description="Fin Kod")],
    db: AsyncSession = Depends(get_db)
):
    return await reject_app_user(fin_kod, db)

@router.get("/app-wait-users")
async def get_app_wait_users_end(
    db: AsyncSession = Depends(get_db)
):
    return await app_wait_users(db)

@router.post("/send-otp/{fin_kod}")
async def send_otp_endpoint(
    fin_kod: Annotated[str, Path(..., description="Fin Kod")],
    db: AsyncSession = Depends(get_db)
):
    return await send_otp(fin_kod, db)

@router.post("/validate-otp/{fin_kod}/{otp}")
async def validate_otp_endpoint(
    fin_kod: Annotated[str, Path(..., description="Fin Kod")],
    otp: Annotated[str, Path(..., description="OTP")],
    db: AsyncSession = Depends(get_db)
):
    return await validate_otp(fin_kod, otp, db)

@router.post("/reset-password")
async def reset_pass_endpoint(
    request: ResetPassword,
    db: AsyncSession = Depends(get_db)
):
    return await reset_password(request, db)