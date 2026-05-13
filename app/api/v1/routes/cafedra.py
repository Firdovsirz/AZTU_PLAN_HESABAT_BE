from typing import Annotated
from app.crud.cafedra import *
from fastapi import Path, Request
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_required import token_required
from app.utils.limiter import limiter, register_limiter

router = APIRouter()

@router.get("/lms/cafedras")
@limiter.limit("1/minute")
async def get_fac_lms_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_cafedras_from_lms(db)

@router.get("/cafedras/{faculty_code}")
@limiter.limit("100/minute")
async def cafedras_by_fac(
    request: Request,
    faculty_code:  Annotated[str, Path(..., description="Faculty Code")],
    db: AsyncSession = Depends(get_db),
    # _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_cafedras_by_faculty_code(faculty_code, db)

@router.get("/cafedra/{cafedra_code}")
@limiter.limit("100/minute")
async def get_caf_details_endpoint(
    request: Request,
    cafedra_code:   Annotated[str, Path(..., description="Cafedra Code")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_caf_details(cafedra_code, db)

@router.put("/update/cafedra/{cafedra_code}/{cafedra_name}")
@limiter.limit("30/minute")
async def update_cafedra_endpoint(
    request: Request,
    cafedra_code: Annotated[str, Path(..., description="Cafedra Code")],
    cafedra_name: Annotated[str, Path(..., description="Cafedra Name")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await update_cafedra_name(cafedra_code, cafedra_name, db)

@router.delete("/delete/cafedra/{cafedra_code}")
@limiter.limit("30/minute")
async def delete_cafedra_endpoint(
    request: Request,
    cafedra_code: Annotated[str, Path(..., description="Cafedra Code")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await delete_cafedra(cafedra_code, db)

@router.get("/cafedra/{cafedra_code}/users/{start}/{end}")
@limiter.limit("10/minute")
async def get_cafedra_users_endpoint(
    request: Request,
    start: int,
    end: int,
    cafedra_code:   Annotated[str, Path(..., description="Cafedra Code")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await cafedra_users(cafedra_code, db, start, end)