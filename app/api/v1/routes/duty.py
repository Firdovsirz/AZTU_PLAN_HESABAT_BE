from app.crud.duty import *
from typing import Annotated
from fastapi import Path, Request
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.utils.limiter import limiter
from fastapi import APIRouter, Depends, Query
from app.utils.jwt_required import token_required

router = APIRouter()

@router.get("/duties")
@limiter.limit("500/minute")
async def get_duties_endpoint(
    request: Request,
    org_type: str | None = Query(None, description="faculty | department"),
    db: Session = Depends(get_db),
    # _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_duties(db, org_type)

@router.get("/duty/{duty_code}")
@limiter.limit("500/minute")
async def get_duty_by_code_endpoint(
    request: Request,
    duty_code: Annotated[str, Path(..., description="Duty Code")],
    db: Session = Depends(get_db),
    # _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_duty_by_code(duty_code, db)

@router.post("/add-duty")
@limiter.limit("300/minute")
async def add_duty_endpoint(
    request: Request,
    duty_name: str = Query(..., description="Name of the duty"),
    org_type: str = Query("faculty", description="faculty | department"),
    db: Session = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await create_duty(duty_name, db, org_type)

@router.put("/update/duty/{duty_code}/{duty_name}")
@limiter.limit("300/minute")
async def update_duty_endpoint(
    request: Request,
    duty_code: Annotated[int, Path(..., description="Duty Code")],
    duty_name: Annotated[str, Path(..., description="Duty Name")],
    org_type: str | None = Query(None, description="faculty | department"),
    db: Session = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await update_duty(duty_code, duty_name, db, org_type)

@router.delete("/delete/duty/{duty_code}")
@limiter.limit("300/minute")
async def delete_duty_endpoint(
    request: Request,
    duty_code: Annotated[int, Path(..., description="Duty Code")],
    db: Session = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await delete_duty(duty_code, db)