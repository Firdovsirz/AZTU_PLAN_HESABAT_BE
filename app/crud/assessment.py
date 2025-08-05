from fastapi import Depends
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from app.models.assessment_model import Assessment
from app.api.v1.schemas.assessment_schema import CreateAssessment

def create_assessment(
        form_data: CreateAssessment = Depends(CreateAssessment.as_form),
        db: Session = Depends(get_db)
):
    try:
        new_assessment = Assessment(
            assessment_score=form_data.assessment_score,
            score_name=form_data.score_name,
            score_desc=form_data.score_desc,
            created_at=datetime.utcnow()
        )

        db.add(new_assessment)
        db.commit()
        db.refresh(new_assessment)

        return JSONResponse(content={
            "status": 201,
            "message": "Assessment created successfully."
        }, status_code=201)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
def get_assessments(db: Session = Depends(get_db)):
    try:
        assessments = db.query(Assessment).all()

        if not assessments:
            return JSONResponse(content={
                "statusCode": 204,
                "message": "No assassment found."
            }, status_code=204)
        
        return JSONResponse(content={
            "statusCode": 200,
            "message": "Assessments detched successfully.",
            "assessments": [
                {
                    "assessment_score": assessment.assessment_score,
                    "score_name": assessment.score_name,
                    "score_desc": assessment.score_desc
                } for assessment in assessments
            ]
        })
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)