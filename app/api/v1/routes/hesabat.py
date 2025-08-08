from fastapi import Path
from typing import Annotated
from app.crud.hesabat import *
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.schemas.hesabat_schema import CreateHesabat

router = APIRouter()

@router.get("/hesabat/{fin_kod}/{start}/{end}")
async def get_hesabat_by_fin_kod_endpoint(
    fin_kod:  Annotated[str, Path(..., description="Fin Kod")],
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_hesabat_by_fin_kod(fin_kod, db, start, end)

@router.get("/hesabat/plan/{serial_number}")
async def get_hesabat_by_fin_kod_endpoint(
    serial_number:  Annotated[str, Path(..., description="Serial Number")],
    db: AsyncSession = Depends(get_db)
):
    return await get_hesabat_by_serial_number(serial_number, db)

@router.post("/submit-hesabat")
async def submit_hesabat_endpoint(
    form_data: CreateHesabat = Depends(CreateHesabat.as_form),
    db: AsyncSession = Depends(get_db)
):
    return await submit_hesabat(form_data, db)

@router.get("/doc/{work_plan_serial_number}/{doc_name}")
async def get_doc_endpoint(
    serial_number: Annotated[str, Path(..., description="Work Serial Number")],
    db: AsyncSession = Depends(get_db)
):
    return await get_doc_by_serial_number(serial_number, db)