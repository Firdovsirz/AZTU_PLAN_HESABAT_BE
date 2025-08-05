from fastapi import Path
from app.crud.auth import *
from typing import Annotated
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter
from app.api.v1.schemas.auth_schema import AuthCreate, Signin

router = APIRouter()

dependencies=[Depends(RateLimiter(times=100, seconds=60))]


@router.post("/signup", dependencies=[Depends(RateLimiter(times = 100, seconds=60))])
def signup_endpoint(
    form_data: AuthCreate = Depends(AuthCreate.as_form),
    db: Session = Depends(get_db)
):
    return signup(form_data, db)

@router.post("/signin")
def signin_endpoint(
    credentials: Signin,
    db: Session = Depends(get_db)
):
    return signin(credentials,db)

@router.post("/approve-user/{fin_kod}")
def approve_user_endpoint(
    fin_kod: Annotated[str, Path(..., description="Fin Kod")],
    db: Session = Depends(get_db)
):
    return approve_user(fin_kod, db)

@router.delete("/reject-user/{fin_kod}")
def approve_user_endpoint(
    fin_kod: Annotated[str, Path(..., description="Fin Kod")],
    db: Session = Depends(get_db)
):
    return reject_app_user(fin_kod, db)

@router.get("/app-wait-users")
def get_app_wait_users_end(
    db: Session = Depends(get_db)
):
    return app_wait_users(db)