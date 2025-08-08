from datetime import datetime
from app.db.session import get_db
from fastapi import Depends, status
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.assessment_model import Assessment
from app.api.v1.schemas.assessment_schema import CreateAssessment

async def create_assessment(
        form_data: CreateAssessment,
        db: AsyncSession = Depends(get_db)
):
    try:
        if not all([form_data.assessment_score, form_data.score_name, form_data.score_desc]):

            return JSONResponse(
                content={
                    "status": 400,
                    "message": "Missing required fields."
                }, status_code=status.HTTP_400_BAD_REQUEST
            )

        new_assessment = Assessment(
            assessment_score=form_data.assessment_score,
            score_name=form_data.score_name,
            score_desc=form_data.score_desc,
            created_at=datetime.utcnow()
        )

        db.add(new_assessment)
        await db.commit()
        await db.refresh(new_assessment)

        return JSONResponse(
            content={
                "status": 201,
                "message": "Assessment created successfully."
            }, status_code=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def get_assessments(db: AsyncSession = Depends(get_db)):
    try:
        fetched_assessments = await db.execute(
            select(Assessment)
        )

        assessments = fetched_assessments.scalars().all()

        if not assessments:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No assassment found."
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Assessments detched successfully.",
                "assessments": [
                    {
                        "assessment_score": assessment.assessment_score,
                        "score_name": assessment.score_name,
                        "score_desc": assessment.score_desc
                    } for assessment in assessments
                ]
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def get_assessment_by_score(
    assessment_score: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_assessment = await db.execute(
            select(Assessment)
            .where(Assessment.assessment_score == assessment_score)
        )

        exist_assessment = fetched_assessment.scalar_one_or_none()

        if not exist_assessment:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Assessment not found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Assessment fetched successfully.",
                "assessment": {
                    "assessment_score": exist_assessment.assessment_score,
                    "score_name": exist_assessment.score_name,
                    "score_desc": exist_assessment.score_desc,
                }
            }
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def delete_assessment(
    assessment_score: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_assessment = await db.execute(
            select(Assessment)
            .where(Assessment.assessment_score == assessment_score)
        )

        exist_assessment = fetched_assessment.scalar_one_or_none()

        if not exist_assessment:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Assessment not found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        await db.delete(exist_assessment)
        await db.commit()

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Assessment deleted successfully."
            }
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )