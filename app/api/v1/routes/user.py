from fastapi import Path
from app.crud.user import *
from typing import Annotated
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/dekans/{start}/{end}")
async def get_dekans(
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db)
):
    return await dekans(db, start, end)

@router.get("/caf-directors/{start}/{end}")
async def get_caf_directors(
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db)
):
    return await caf_directors(db, start, end)

@router.get("/users/{start}/{end}")
async def get_all_users(
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db)
):
    return await all_users(db, start, end)

@router.get("/user/{fin_kod}")
async def get_user_endpoint(
    fin_kod: Annotated[str, Path(..., description="Fin kod")],
    db: AsyncSession = Depends(get_db)
):
    return await get_user_by_fin_kod(fin_kod, db)

@router.get("/users/execution/{start}/{end}")
async def get_users_endpoint(
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_execution_users(db, start=start, end=end)

@router.get("/users/app-waiting")
async def get_app_waiting_users_endpoint(
    db: AsyncSession = Depends(get_db)
):
    return await get_app_waiting_users(db)