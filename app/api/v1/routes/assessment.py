from fastapi import Path
from typing import Annotated
from app.crud.assessment import *
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.schemas.assessment_schema import CreateAssessment

router = APIRouter()

@router.post("/create-assessment")
async def create_assessment_endpoint(
    form_data: CreateAssessment,
    db: AsyncSession = Depends(get_db)
):
    return await create_assessment(form_data, db)

@router.get("/assessments")
async def get_assessments_endpoint(db: AsyncSession = Depends(get_db)):
    return await get_assessments(db)

@router.get("/assessment/{assessment_score}")
async def get_assessment(
    assessment_score: Annotated[int, Path(..., description="Assessment score")],
    db: AsyncSession = Depends(get_db)
):
    return await get_assessment_by_score(assessment_score, db)

@router.delete("/delete/assessment/{assessment_score}")
async def del_assessment(
    assessment_score: Annotated[int, Path(..., description="Assessment score")],
    db: AsyncSession = Depends(get_db)
):
    return await delete_assessment(assessment_score, db)