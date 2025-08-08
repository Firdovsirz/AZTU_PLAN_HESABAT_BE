from fastapi import Path
from typing import Annotated
from app.crud.faculty import *
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/lms/faculties")
async def get_fac_lms_endpoint(db: AsyncSession = Depends(get_db)):
    return await get_faculties_from_lms(db)

@router.get("/faculties")
async def get_faculties(db: AsyncSession = Depends(get_db)):
    return await get_faculties_from_local(db)

@router.get("/faculties/{faculty_code}")
async def get_fac_name_endpoint(
    faculty_code: Annotated[str, Path(..., description="Faculty Code")],
    db: AsyncSession = Depends(get_db)
):
    return await get_fac_name(faculty_code, db)