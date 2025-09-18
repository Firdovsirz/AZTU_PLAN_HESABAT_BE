from typing import Annotated
from fastapi import Path, Request
from app.crud.assessment import *
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_required import token_required
from app.api.v1.schemas.assessment_schema import CreateAssessment
from app.utils.limiter import limiter, register_limiter

router = APIRouter()

@router.get("/assessments")
@limiter.limit("30/second")
async def get_assessments_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_assessments(db)

@router.get("/assessment/{assessment_score}")
@limiter.limit("30/second")
async def get_assessment(
    request: Request,
    assessment_score: Annotated[int, Path(..., description="Assessment score")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_assessment_by_score(assessment_score, db)

@router.post("/create-assessment")
@limiter.limit("5/minute")
async def create_assessment_endpoint(
    request: Request,
    form_data: CreateAssessment,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await create_assessment(form_data, db)

@router.delete("/delete/assessment/{assessment_score}")
@limiter.limit("5/minute")
async def del_assessment(
    request: Request,
    assessment_score: Annotated[int, Path(..., description="Assessment score")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await delete_assessment(assessment_score, db)