from fastapi import Path
from app.crud.plan import *
from typing import Annotated
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.schemas.plan_schema import CreatePlan

router = APIRouter()

@router.post("/create-plan")
async def create_plan_endpoint(
    form_data: CreatePlan = Depends(CreatePlan.as_form),
    db: AsyncSession = Depends(get_db)
):
    return await create_plan(form_data, db)

@router.get("/plan/{fin_kod}/{start}/{end}")
async def get_plan_by_fin_kod_endpoint(
    fin_kod: Annotated[str, Path(..., description="Faculty Code")],
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_plan_by_fin_kod(fin_kod, start, end, db)