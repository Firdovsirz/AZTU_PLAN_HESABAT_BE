from typing import Annotated
from app.crud.hesabat import *
from fastapi import Path, Request
from app.db.session import get_db
from app.utils.limiter import limiter
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Security
from app.utils.jwt_required import token_required
from app.api.v1.schemas.hesabat_schema import SetAssessmentSchema, UpdateAssessmentScore, CreateHesabat

router = APIRouter()
bearer_scheme = HTTPBearer()

@router.get("/submitted-hesabats/{start}/{end}")
@limiter.limit("10/minute")
async def submitted_hesabats_endpoint(
    request: Request,
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1])),
    swagger_token: str = Security(bearer_scheme)
):
    return await submitted_hesabats(db, start, end)

@router.get("/hesabat/{fin_kod}/{start}/{end}")
@limiter.limit("10/minute")
async def get_hesabat_by_fin_kod_endpoint(
    request: Request,
    fin_kod:  Annotated[str, Path(..., description="Fin Kod")],
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_hesabat_by_fin_kod(fin_kod, db, start, end)

@router.get("/hesabat/plan/{serial_number}")
@limiter.limit("50/minute")
async def get_hesabat_by_fin_kod_endpoint(
    request: Request,
    serial_number:  Annotated[str, Path(..., description="Serial Number")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_hesabat_by_serial_number(serial_number, db)

@router.post("/done-hesabat/{work_plan_serial_number}")
@limiter.limit("10/minute")
async def done_hesabat_endpoint(
    request: Request,
    work_plan_serial_number: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await done_hesabat(work_plan_serial_number, db)

@router.post("/submit-hesabat")
@limiter.limit("50/minute")
async def submit_hesabat_endpoint(
    request: Request,
    form_data: CreateHesabat = Depends(CreateHesabat.as_form),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await submit_hesabat(form_data, db)

@router.get("/doc/{work_plan_serial_number}/{doc_name}")
@limiter.limit("50/minute")
async def get_doc_endpoint(
    request: Request,
    serial_number: Annotated[str, Path(..., description="Work Serial Number")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_doc_by_serial_number(serial_number, db)

@router.post("/assessment")
@limiter.limit("10/minute")
async def set_assessment(
    request: Request,
    assessment_data: SetAssessmentSchema,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await add_assessment(assessment_data, db)

@router.patch("/assessment/update")
@limiter.limit("10/minute")
async def update_assessment_endpoint(
    request: Request,
    assessment_data: UpdateAssessmentScore,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await update_assessment(assessment_data, db)

@router.get("/archive/{start}/{end}")
@limiter.limit("10/minute")
async def archive_endpoint(
    request: Request,
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_archive(db, start, end)

@router.delete("/hesabat/{work_plan_serial_number}/delete")
@limiter.limit("10/minute")
async def delete_hesabat_endpoint(
    request: Request,
    work_plan_serial_number: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await delete_hesabat(work_plan_serial_number, db)