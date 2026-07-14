from app.crud.plan import *
from typing import Annotated
from fastapi import Path, Request
from app.db.session import get_db
from app.utils.limiter import limiter
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_required import token_required
from app.api.v1.schemas.plan_schema import CreatePlan, AddActivityToPlan
from app.api.v1.schemas.request_schema import AdminEditTarget

router = APIRouter()

@router.get("/structure-plan-counts")
@limiter.limit("500/minute")
async def structure_plan_counts_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await structure_plan_counts(db)


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


# --- Admin direct actions --------------------------------------------------
# The admin edits/deletes a plan directly (no request); the owner is notified.

@router.patch("/plan/{work_plan_serial_number}/edit")
@limiter.limit("100/minute")
async def admin_edit_plan_endpoint(
    request: Request,
    work_plan_serial_number: Annotated[str, Path(..., description="Work Plan Serial Number")],
    body: AdminEditTarget,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await admin_edit_plan(work_plan_serial_number, body.changes, db)


@router.delete("/plan/{work_plan_serial_number}/delete")
@limiter.limit("100/minute")
async def admin_delete_plan_endpoint(
    request: Request,
    work_plan_serial_number: Annotated[str, Path(..., description="Work Plan Serial Number")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await admin_delete_plan(work_plan_serial_number, db)