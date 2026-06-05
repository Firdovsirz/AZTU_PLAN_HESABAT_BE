from app.crud.plan import *
from typing import Annotated
from fastapi import Path, Request
from app.db.session import get_db
from app.utils.limiter import limiter
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_required import token_required
from app.api.v1.schemas.plan_schema import CreatePlan, AddActivityToPlan

router = APIRouter()

@router.get("/plans/{start}/{end}")
@limiter.limit("500/second")
async def all_plans_endpoint(
    request: Request,
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await all_plans(db, start, end)


@router.get("/plan/{fin_kod}/{start}/{end}")
@limiter.limit("500/second")
async def get_plan_by_fin_kod_endpoint(
    request: Request,
    fin_kod: Annotated[str, Path(..., description="Faculty Code")],
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_plan_by_fin_kod(fin_kod, start, end, db)

@router.get("/single-plan/{work_plan_serial_number}")
@limiter.limit("500/second")
async def get_single_plan(
    request: Request,
    work_plan_serial_number: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_plan_by_serial_number(work_plan_serial_number, db)

@router.post("/create-plan")
@limiter.limit("200/second")
async def create_plan_endpoint(
    request: Request,
    form_data: CreatePlan = Depends(CreatePlan.as_form),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await create_plan(form_data, db)

@router.post("/update/plan")
@limiter.limit("500/second")
async def update_plan_endpoint(
    request: Request,
    req_data: AddActivityToPlan,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await add_activity_to_plan(req_data, db)