from app.crud.plan import *
from typing import Annotated
from fastapi import Path, Request
from app.db.session import get_db
from app.utils.limiter import limiter
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_required import token_required
from app.api.v1.schemas.plan_schema import CreatePlan

router = APIRouter()

@router.get("/plans/{start}/{end}")
@limiter.limit("50/minute")
async def all_plans_endpoint(
    request: Request,
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await all_plans(db, start, end)

@router.post("/create-plan")
@limiter.limit("50/minute")
async def create_plan_endpoint(
    request: Request,
    form_data: CreatePlan = Depends(CreatePlan.as_form),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await create_plan(form_data, db)

@router.get("/plan/{fin_kod}/{start}/{end}")
@limiter.limit("10/minute")
async def get_plan_by_fin_kod_endpoint(
    request: Request,
    fin_kod: Annotated[str, Path(..., description="Faculty Code")],
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_plan_by_fin_kod(fin_kod, start, end, db)