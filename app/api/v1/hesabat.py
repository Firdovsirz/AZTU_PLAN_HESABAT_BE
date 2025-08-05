from fastapi import Path
from typing import Annotated
from app.crud.hesabat import *
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.api.v1.schemas.hesabat_schema import CreateHesabat

router = APIRouter()

@router.get("/hesabat/{fin_kod}")
def get_hesabat_by_fin_kod_endpoint(
    fin_kod:  Annotated[str, Path(..., description="Fin Kod")],
    db: Session = Depends(get_db)
):
    return get_hesabat_by_fin_kod(fin_kod, db)

@router.get("/hesabat/plan/{serial_number}")
def get_hesabat_by_fin_kod_endpoint(
    serial_number:  Annotated[str, Path(..., description="Serial Number")],
    db: Session = Depends(get_db)
):
    return get_hesabat_by_serial_number(serial_number, db)

@router.post("/submit-hesabat")
def submit_hesabat_endpoint(
    form_data: CreateHesabat = Depends(CreateHesabat.as_form),
    db: Session = Depends(get_db)
):
    return submit_hesabat(form_data, db)

@router.get("/doc/{work_plan_serial_number}/{doc_name}")
def get_doc_endpoint(
    serial_number: Annotated[str, Path(..., description="Work Serial Number")],
    db: Session = Depends(get_db)
):
    return get_doc_by_serial_number(serial_number, db)