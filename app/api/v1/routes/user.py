from fastapi import Path
from app.crud.user import *
from typing import Annotated
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Get dekans by pagination

@router.get("/dekans/{start}/{end}")
async def get_dekans(
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db)
):
    return await dekans(db, start, end)

# Get single dekan by faculty code

@router.get("/dekan/{faculty_code}")
async def get_dekan_endpoint(
    faculty_code: str,
    db: AsyncSession = Depends(get_db)
):
    return await get_dekan(faculty_code, db)

# Get cafedra directors by pagination

@router.get("/caf-directors/{start}/{end}")
async def get_caf_directors(
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db)
):
    return await caf_directors(db, start, end)

# Get single cafedra director by cafedra code

@router.get("/caf-director/{cafedra_code}")
async def get_caf_director_endpoint(
    cafedra_code: str,
    db: AsyncSession = Depends(get_db)
):
    return await caf_director(cafedra_code, db)

# Get users by pagination

@router.get("/users/{start}/{end}")
async def get_all_users(
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db)
):
    return await all_users(db, start, end)

# Get user by fin kod

@router.get("/user/{fin_kod}")
async def get_user_endpoint(
    fin_kod: Annotated[str, Path(..., description="Fin kod")],
    db: AsyncSession = Depends(get_db)
):
    return await get_user_by_fin_kod(fin_kod, db)

# Get execution users by pagination

@router.get("/users/execution/{start}/{end}")
async def get_users_endpoint(
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_execution_users(db, start=start, end=end)

# Get all approve waiting users

@router.get("/users/app-waiting")
async def get_app_waiting_users_endpoint(
    db: AsyncSession = Depends(get_db)
):
    return await get_app_waiting_users(db)