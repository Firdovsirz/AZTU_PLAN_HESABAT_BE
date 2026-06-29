from typing import Annotated
from app.crud.faculty import *
from fastapi import Path, Request, Query
from app.db.session import get_db
from app.utils.limiter import limiter
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_required import token_required
from app.utils.api_key_validator import get_api_key

router = APIRouter()

@router.post("/add-faculty")
@limiter.limit("300/minute")
async def add_faculty_endpoint(
    request: Request,
    faculty_code: str = Query(..., description="Faculty Code"),
    faculty_name: str = Query(..., description="Faculty Name"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await create_faculty(faculty_code, faculty_name, db)

@router.get("/lms/faculties")
@limiter.limit("1/minute")
async def get_fac_lms_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_faculties_from_lms(db)

@router.get("/faculties")
@limiter.limit("500/minute")
async def get_faculties(
    request: Request,
    db: AsyncSession = Depends(get_db),
    # _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_faculties_from_local(db)

@router.put("/update/faculty/{faculty_code}/{faculty_name}")
@limiter.limit("300/minute")
async def update_faculty_endpoint(
    request: Request,
    faculty_code: Annotated[str, Path(..., description="Faculty Code")],
    faculty_name: Annotated[str, Path(..., description="Faculty Name")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await update_faculty_name(faculty_code, faculty_name, db)

@router.delete("/delete/faculty/{faculty_code}")
@limiter.limit("300/minute")
async def delete_faculty_endpoint(
    request: Request,
    faculty_code: Annotated[str, Path(..., description="Faculty Code")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await delete_faculty(faculty_code, db)

@router.get("/faculties/{faculty_code}")
@limiter.limit("500/minute")
async def get_fac_name_endpoint(
    request: Request,
    faculty_code: Annotated[str, Path(..., description="Faculty Code")],
    db: AsyncSession = Depends(get_db),
    # _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_fac_name(faculty_code, db)

@router.get("/faculty/{faculty_code}/plans-hesabats")
@limiter.limit("500/minute")
async def faculty_plans_hesabats_endpoint(
    request: Request,
    faculty_code: Annotated[str, Path(..., description="Faculty Code")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await faculty_plans_hesabats(faculty_code, db)