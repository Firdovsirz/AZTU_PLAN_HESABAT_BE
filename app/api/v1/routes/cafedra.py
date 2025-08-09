from fastapi import Path
from typing import Annotated
from app.crud.cafedra import *
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/lms/cafedras")
async def get_fac_lms_endpoint(db: AsyncSession = Depends(get_db)):
    return await get_cafedras_from_lms(db)

@router.get("/cafedras/{faculty_code}")
async def cafedras_by_fac(
    faculty_code:  Annotated[str, Path(..., description="Faculty Code")],
    db: AsyncSession = Depends(get_db)
):
    return await get_cafedras_by_faculty_code(faculty_code, db)

@router.get("/cafedra/{cafedra_code}")
async def get_caf_details_endpoint(
    cafedra_code:   Annotated[str, Path(..., description="Cafedra Code")],
    db: AsyncSession = Depends(get_db)
):
    return await get_caf_details(cafedra_code, db)

@router.get("/cafedra/{cafedra_code}/users/{start}/{end}")
async def get_cafedra_users_endpoint(
    start: int,
    end: int,
    cafedra_code:   Annotated[str, Path(..., description="Cafedra Code")],
    db: AsyncSession = Depends(get_db),
):
    return await cafedra_users(cafedra_code, db, start, end)