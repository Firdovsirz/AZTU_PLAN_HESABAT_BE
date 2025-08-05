from fastapi import Path
from app.crud.plan import *
from typing import Annotated
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.api.v1.schemas.plan_schema import CreatePlan

router = APIRouter()

@router.post("/create-plan")
def create_plan_endpoint(
    form_data: CreatePlan = Depends(CreatePlan.as_form),
    db: Session = Depends(get_db)
):
    return create_plan(form_data, db)

@router.get("/plan/{fin_kod}")
def get_plan_by_fin_kod_endpoint(
    fin_kod: Annotated[str, Path(..., description="Faculty Code")],
    db: Session = Depends(get_db)
):
    return get_plan_by_fin_kod(fin_kod, db)