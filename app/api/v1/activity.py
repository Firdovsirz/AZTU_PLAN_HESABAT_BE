from fastapi import Path
from typing import Annotated
from app.crud.activity import *
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query

router = APIRouter()

@router.post("/add-activity/{activity_name}")
def add_activity_endpoint(
    activity_name: str =  Annotated[str, Path(..., description="Activity Name")],
    db: Session = Depends(get_db)
):
    return create_activity(activity_name, db)

@router.get("/activities")
def get_activity_endpoint(db: Session = Depends(get_db)):
    return get_activity(db)

@router.get("/activity/{activity_type_code}")
def get_act_by_code_endpoint(
    activity_type_code: str =  Annotated[str, Path(..., description="Activity Code")],
    db: Session = Depends(get_db)
):
    return get_activity_name_by_code(activity_type_code, db)