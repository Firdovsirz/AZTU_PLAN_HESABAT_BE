from app.crud.assessment import *
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.api.v1.schemas.assessment_schema import CreateAssessment

router = APIRouter()

@router.post("/create-assessment")
def signup_endpoint(
    form_data: CreateAssessment = Depends(CreateAssessment.as_form),
    db: Session = Depends(get_db)
):
    return create_assessment(form_data, db)

@router.get("/assessments")
def get_assessments_endpoint(db: Session = Depends(get_db)):
    return get_assessments(db)