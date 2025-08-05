from fastapi import Path
from typing import Annotated
from app.crud.cafedra import *
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/lms/cafedras")
def get_fac_lms_endpoint(db: Session = Depends(get_db)):
    return get_cafedras_from_lms(db)

@router.get("/cafedras/{faculty_code}")
def cafedras_by_fac(
    faculty_code:  Annotated[str, Path(..., description="Faculty Code")],
    db: Session = Depends(get_db)
):
    return get_cafedras_by_faculty_code(faculty_code, db)

@router.get("/cafedra/{cafedra_code}")
def get_caf_name_endpoint(
    cafedra_code:   Annotated[str, Path(..., description="Cafedra Code")],
    db: Session = Depends(get_db)
):
    return get_caf_name(cafedra_code, db)

@router.get("/cafedra/{cafedra_code}/users")
def get_cafedra_users_endpoint(
    cafedra_code:   Annotated[str, Path(..., description="Cafedra Code")],
    db: Session = Depends(get_db)
):
    return cafedra_users(cafedra_code, db)