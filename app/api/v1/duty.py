from fastapi import Path
from app.crud.duty import *
from typing import Annotated
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query

router = APIRouter()

@router.post("/add-duty")
def add_duty_endpoint(
    duty_name: str = Query(..., description="Name of the duty"),
    db: Session = Depends(get_db)
):
    return create_duty(duty_name, db)

@router.get("/duties")
def get_duties_endpoint(db: Session = Depends(get_db)):
    return get_duties(db)

@router.get("/duty/{duty_code}")
def get_duty_by_code_endpoint(
    duty_code: Annotated[str, Path(..., description="Duty Code")],
    db: Session = Depends(get_db)
):
    return get_duty_by_code(duty_code, db)