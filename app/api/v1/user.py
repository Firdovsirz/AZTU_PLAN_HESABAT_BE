from fastapi import Path
from app.crud.user import *
from typing import Annotated
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/user/{fin_kod}")
def get_user_endpoint(
    fin_kod: Annotated[str, Path(..., description="Fin kod")],
    db: Session = Depends(get_db)
):
    return get_user_by_fin_kod(fin_kod, db)

# @router.get("/users/execution")
# def get_users_enpoint(
#     db: Session = Depends(get_db)
# ):
#     return get_users(db)

@router.get("/users/execution")
def get_users_enpoint(
    db: Session = Depends(get_db)
):
    return get_execution_users(db)

@router.get("/users/app-waiting")
def get_app_waiting_users_endpoint(
    db: Session = Depends(get_db)
):
    return get_app_waiting_users(db)