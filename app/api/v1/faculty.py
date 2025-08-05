from fastapi import Path
from typing import Annotated
from app.crud.faculty import *
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/lms/faculties")
def get_fac_lms_endpoint(db: Session = Depends(get_db)):
    return get_faculties_from_lms(db)

@router.get("/faculties")
def get_faculties(db: Session = Depends(get_db)):
    return get_faculties_from_local(db)

@router.get("/faculties/{faculty_code}")
def get_fac_name_endpoint(
    faculty_code: Annotated[str, Path(..., description="Faculty Code")],
    db: Session = Depends(get_db)
):
    return get_fac_name(faculty_code, db)