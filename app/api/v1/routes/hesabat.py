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
from app.api.v1.schemas.request_schema import AdminEditTarget

router = APIRouter()
bearer_scheme = HTTPBearer()

@router.get("/submitted-hesabats/{start}/{end}")
@limiter.limit("500/second")
async def submitted_hesabats_endpoint(
    request: Request,
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1])),
    # swagger_token: str = Security(bearer_scheme)
):
    return await submitted_hesabats(db, start, end)

@router.get("/hesabat/{fin_kod}/{start}/{end}")
@limiter.limit("500/second")
async def get_hesabat_by_fin_kod_endpoint(
    request: Request,
    fin_kod:  Annotated[str, Path(..., description="Fin Kod")],
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_hesabat_by_fin_kod(fin_kod, start, end, db)

@router.get("/hesabat/plan/{serial_number}")
@limiter.limit("500/second")
async def get_hesabat_by_fin_kod_endpoint(
    request: Request,
    serial_number:  Annotated[str, Path(..., description="Serial Number")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_hesabat_by_serial_number(serial_number, db)


@router.get("/doc/{work_plan_serial_number}/{doc_name}")
@limiter.limit("500/second")
async def get_doc_endpoint(
    request: Request,
    work_plan_serial_number: Annotated[str, Path(..., description="Work Serial Number")],
    doc_name: Annotated[str, Path(..., description="Document Name")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_doc_by_serial_number(work_plan_serial_number, db)

@router.get("/secure-doc/{work_plan_serial_number}/{doc_name}")
@limiter.limit("500/minute")
async def secure_doc_endpoint(
    request: Request,
    work_plan_serial_number: Annotated[str, Path(..., description="Work Plan Serial Number")],
    doc_name: Annotated[str, Path(..., description="Document file name")],
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await serve_report_doc(work_plan_serial_number, doc_name)

@router.get("/archive/{start}/{end}")
@limiter.limit("100/minute")
async def archive_endpoint(
    request: Request,
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await get_archive(db, start, end)

@router.post("/done-hesabat/{work_plan_serial_number}")
@limiter.limit("100/minute")
async def done_hesabat_endpoint(
    request: Request,
    work_plan_serial_number: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await done_hesabat(work_plan_serial_number, db)

@router.post("/submit-hesabat")
@limiter.limit("200/second")
async def submit_hesabat_endpoint(
    request: Request,
    form_data: CreateHesabat = Depends(CreateHesabat.as_form),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await submit_hesabat(form_data, db)

@router.post("/hesabat/assessment")
@limiter.limit("100/second")
async def set_assessment(
    request: Request,
    assessment_data: SetAssessmentSchema,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await add_assessment(assessment_data, db)

@router.patch("/hesabat/assessment/update")
@limiter.limit("200/second")
async def update_assessment_endpoint(
    request: Request,
    assessment_data: UpdateAssessmentScore,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await update_assessment(assessment_data, db)

@router.patch("/hesabat/{work_plan_serial_number}/edit")
@limiter.limit("100/minute")
async def admin_edit_hesabat_endpoint(
    request: Request,
    work_plan_serial_number: Annotated[str, Path(..., description="Work Plan Serial Number")],
    body: AdminEditTarget,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await admin_edit_hesabat(work_plan_serial_number, body.changes, db)


@router.delete("/hesabat/{work_plan_serial_number}/delete")
@limiter.limit("200/second")
async def delete_hesabat_endpoint(
    request: Request,
    work_plan_serial_number: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await delete_hesabat(work_plan_serial_number, db)